import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import httpx

from app.database import get_db
from app.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    verify_token, hash_token, get_current_user,
    SECRET_KEY, ALGORITHM,
)
from app.models import User, RefreshToken
from app.schemas import (
    UserCreate, TokenResponse, LoginRequest, GoogleAuthRequest,
    ForgotPasswordRequest, ResetPasswordRequest, UserResponse,
)
from app import crud
from app.email_service import send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")

REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
_IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development").lower() != "development"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Define o refresh token como HttpOnly cookie (não acessível via JS)."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_IS_PRODUCTION,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )


def _create_tokens_for_user(db: Session, user: User) -> dict:
    """Helper: gera par de tokens e persiste refresh token no banco."""
    access_token = create_access_token({"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token({"sub": user.id})

    # Armazenar hash do refresh token no banco (RN-014)
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    crud.create_refresh_token(db, token_record)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: UserCreate, response: Response, db: Session = Depends(get_db)):
    """RF-08: Cadastro de usuário com nome, email e senha."""
    existing = crud.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email já cadastrado")  # RN-011

    user = User(
        nome=data.nome,
        email=data.email,
        password_hash=hash_password(data.password),  # RN-012
    )
    user = crud.create_user(db, user)
    tokens = _create_tokens_for_user(db, user)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return {"access_token": tokens["access_token"], "token_type": tokens["token_type"], "user": user}


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """RF-09: Login com email e senha."""
    user = crud.get_user_by_email(db, data.email)
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")  # Mensagem genérica

    tokens = _create_tokens_for_user(db, user)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return {"access_token": tokens["access_token"], "token_type": tokens["token_type"], "user": user}


@router.post("/google", response_model=TokenResponse)
async def google_auth(data: GoogleAuthRequest, response: Response, db: Session = Depends(get_db)):
    """RF-09: Login com Google OAuth2 (Authorization Code flow)."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google OAuth não configurado")

    # Trocar code por tokens Google via httpx
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": data.code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Código Google inválido")

    google_data = token_response.json()
    id_token = google_data.get("id_token")

    # Decodificar ID token (sem verificação de assinatura — já validado pelo Google)
    from jose import jwt as jose_jwt
    user_info = jose_jwt.get_unverified_claims(id_token)

    google_id = user_info.get("sub")
    email = user_info.get("email")
    nome = user_info.get("name", "")
    avatar_url = user_info.get("picture")

    # Buscar usuário existente por google_id ou email (RN-017: merge)
    user = crud.get_user_by_google_id(db, google_id)
    if not user:
        user = crud.get_user_by_email(db, email)
        if user:
            # Vincular Google a conta existente (merge)
            user.google_id = google_id
            if avatar_url:
                user.avatar_url = avatar_url
            crud.update_user(db, user)
        else:
            # Criar novo usuário via Google
            user = User(
                nome=nome,
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
                email_verified=True,  # Email verificado pelo Google
            )
            user = crud.create_user(db, user)

    tokens = _create_tokens_for_user(db, user)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return {"access_token": tokens["access_token"], "token_type": tokens["token_type"], "user": user}


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(request: Request, response: Response, db: Session = Depends(get_db)):
    """RF-10: Renovar tokens via refresh token (com rotação — RN-014). Lê refresh token do HttpOnly cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token ausente")

    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    # Verificar se token existe no banco (não foi revogado)
    token_hash = hash_token(refresh_token)
    stored_token = crud.get_refresh_token_by_hash(db, token_hash)
    if not stored_token or stored_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expirado ou revogado")

    # Rotação: invalidar token antigo
    crud.delete_refresh_token(db, stored_token)

    # Gerar novo par de tokens
    user = crud.get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    tokens = _create_tokens_for_user(db, user)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return {"access_token": tokens["access_token"], "token_type": tokens["token_type"]}


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RF-10: Logout — invalida refresh token no banco e limpa cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        token_hash = hash_token(refresh_token)
        stored_token = crud.get_refresh_token_by_hash(db, token_hash)
        if stored_token:
            crud.delete_refresh_token(db, stored_token)
    response.delete_cookie(key="refresh_token", path="/api/auth")
    return {"message": "Logout realizado com sucesso"}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """RF-11: Solicitar email de recuperação de senha (RN-016)."""
    # Sempre retorna 200 por segurança (não revela se email existe)
    user = crud.get_user_by_email(db, data.email)
    if user and user.password_hash:
        # Gerar token de reset (JWT com 1h de expiração)
        from jose import jwt as jose_jwt
        reset_token = jose_jwt.encode(
            {"sub": user.id, "type": "reset", "exp": datetime.utcnow() + timedelta(hours=1)},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        send_password_reset_email(user.email, reset_token, user.nome)

    return {"message": "Se o email estiver cadastrado, você receberá um link de recuperação"}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """RF-11: Redefinir senha com token de reset (RN-016)."""
    payload = verify_token(data.token)
    if not payload or payload.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Token de reset inválido ou expirado")

    user = crud.get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=400, detail="Token de reset inválido")

    user.password_hash = hash_password(data.new_password)
    crud.update_user(db, user)

    # Invalidar todos os refresh tokens do usuário (segurança)
    crud.delete_user_refresh_tokens(db, user.id)

    return {"message": "Senha redefinida com sucesso"}
