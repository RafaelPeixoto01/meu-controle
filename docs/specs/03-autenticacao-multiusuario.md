# Spec — Autenticação e Multi-usuário (CR-002)

> Extraído de `docs/03-SPEC.md` no CR-038 (conteúdo original preservado). Índice: [03-SPEC.md](../03-SPEC.md)

## 2b. Detalhamento Tecnico — Autenticacao e Multi-usuario (CR-002)

### Feature: [RF-08/RF-09/RF-10] Autenticacao Backend

#### 2b.1 Descricao Tecnica

Implementa sistema completo de autenticacao: cadastro com email/senha, login com email/senha e Google OAuth2, gestao de sessao com JWT (access token 15min + refresh token 7 dias com rotacao), e isolamento de dados por usuario. Inclui recuperacao de senha via email SendGrid (RF-11).

#### 2b.2 Arquivos

| Acao      | Caminho                                              | Descricao                                                    |
|-----------|------------------------------------------------------|--------------------------------------------------------------|
| Criar     | `backend/app/auth.py`                               | JWT logic, password hashing, get_current_user dependency      |
| Criar     | `backend/app/routers/auth.py`                       | 7 endpoints de autenticacao                                   |
| Criar     | `backend/app/email_service.py`                      | Integracao SendGrid para password reset                       |
| Modificar | `backend/app/models.py`                             | Modelos User e RefreshToken                                   |
| Modificar | `backend/app/schemas.py`                            | Schemas de auth                                               |
| Modificar | `backend/app/crud.py`                               | Funcoes CRUD para User e RefreshToken                         |

#### 2b.3 Interfaces / Types

**Backend — Models (`backend/app/models.py` — secao User e RefreshToken):**

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Nullable para Google-only users
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user = relationship("User", back_populates="refresh_tokens")
```

**Backend — Schemas (`backend/app/schemas.py` — secao Auth):**

```python
# ========== Auth Schemas (CR-002) ==========

class UserCreate(BaseModel):
    """Schema para cadastro de usuario."""
    nome: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Schema para atualizacao de perfil."""
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)


class UserResponse(BaseModel):
    """Schema de resposta para usuario."""
    model_config = {"from_attributes": True}

    id: str
    nome: str
    email: str
    avatar_url: Optional[str]
    email_verified: bool
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Schema para login com email/senha."""
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    """Schema para login com Google OAuth2."""
    code: str


class RefreshTokenRequest(BaseModel):
    """Schema para refresh de token."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Schema de resposta com tokens JWT.
    CR-010: refresh_token nao e mais enviado no body — emitido via HttpOnly cookie (Set-Cookie).
    """
    access_token: str
    refresh_token: Optional[str] = None  # Ausente no body; enviado via Set-Cookie: refresh_token (HttpOnly)
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class ForgotPasswordRequest(BaseModel):
    """Schema para solicitar reset de senha."""
    email: str


class ResetPasswordRequest(BaseModel):
    """Schema para redefinir senha."""
    token: str
    new_password: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    """Schema para trocar senha pelo perfil."""
    current_password: str
    new_password: str = Field(..., min_length=6)
```

#### 2b.4 Logica de Negocio

**`backend/app/auth.py` — Modulo de autenticacao:**

```python
import os
import hashlib
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud

# Configuracao
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    """Hash de senha com bcrypt (RN-012)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha contra hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Cria JWT access token com expiracao de 15 minutos (RN-013)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Cria JWT refresh token com expiracao de 7 dias (RN-013)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Decodifica e valida um JWT. Retorna payload ou None se invalido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Hash SHA-256 de um refresh token para armazenamento seguro no banco."""
    return hashlib.sha256(token.encode()).hexdigest()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency: extrai usuario do JWT access token.
    Usado como Depends(get_current_user) nos endpoints protegidos.
    Retorna instancia User ou lanca HTTPException 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    return user
```

**`backend/app/email_service.py` — Integracao SendGrid:**

```python
import os
import logging

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


def send_password_reset_email(to_email: str, reset_token: str, user_name: str) -> bool:
    """
    Envia email de recuperacao de senha via SendGrid.
    Degradacao graciosa: se SENDGRID_API_KEY nao configurada, loga token e retorna True.
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    if not SENDGRID_API_KEY:
        logger.warning(
            f"SendGrid nao configurado. Token de reset para {to_email}: {reset_token}"
        )
        logger.warning(f"Link de reset: {reset_link}")
        return True

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=SENDGRID_FROM_EMAIL,
            to_emails=to_email,
            subject="Meu Controle - Recuperacao de Senha",
            html_content=f"""
            <h2>Recuperacao de Senha</h2>
            <p>Ola {user_name},</p>
            <p>Voce solicitou a recuperacao de senha. Clique no link abaixo para redefinir:</p>
            <p><a href="{reset_link}">Redefinir minha senha</a></p>
            <p>Este link expira em 1 hora.</p>
            <p>Se voce nao solicitou esta recuperacao, ignore este email.</p>
            """,
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True

    except Exception as e:
        logger.error(f"Erro ao enviar email via SendGrid: {e}")
        return False
```

**CRUD — Funcoes para User e RefreshToken (`backend/app/crud.py` — secao User/RefreshToken):**

```python
from app.models import Expense, Income, User, RefreshToken  # CR-002: User, RefreshToken

# ========== Users (CR-002) ==========

def get_user_by_email(db: Session, email: str) -> User | None:
    """Retorna usuario por email ou None."""
    stmt = select(User).where(User.email == email)
    return db.scalars(stmt).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Retorna usuario por ID ou None."""
    return db.get(User, user_id)


def get_user_by_google_id(db: Session, google_id: str) -> User | None:
    """Retorna usuario por Google ID ou None."""
    stmt = select(User).where(User.google_id == google_id)
    return db.scalars(stmt).first()


def create_user(db: Session, user: User) -> User:
    """Persiste um novo usuario."""
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User) -> User:
    """Persiste alteracoes em um usuario existente."""
    db.commit()
    db.refresh(user)
    return user


# ========== Refresh Tokens (CR-002) ==========

def create_refresh_token(db: Session, token: RefreshToken) -> RefreshToken:
    """Persiste um novo refresh token."""
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_refresh_token_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    """Retorna refresh token pelo hash ou None."""
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    return db.scalars(stmt).first()


def delete_refresh_token(db: Session, token: RefreshToken) -> None:
    """Remove um refresh token (rotacao)."""
    db.delete(token)
    db.commit()


def delete_user_refresh_tokens(db: Session, user_id: str) -> None:
    """Remove todos os refresh tokens de um usuario (logout total)."""
    stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
    tokens = list(db.scalars(stmt).all())
    for token in tokens:
        db.delete(token)
    db.commit()
```

#### 2b.5 API Endpoints

**`backend/app/routers/auth.py`**

```python
import os

from fastapi import APIRouter, Depends, HTTPException, status
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
    RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest, UserResponse,
)
from app import crud
from app.email_service import send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")

REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


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
def register(data: UserCreate, db: Session = Depends(get_db)):
    """RF-08: Cadastro de usuario com nome, email e senha."""
    existing = crud.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email ja cadastrado")  # RN-011

    user = User(
        nome=data.nome,
        email=data.email,
        password_hash=hash_password(data.password),  # RN-012
    )
    user = crud.create_user(db, user)
    tokens = _create_tokens_for_user(db, user)
    return {**tokens, "user": user}


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """RF-09: Login com email e senha."""
    user = crud.get_user_by_email(db, data.email)
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais invalidas")  # Mensagem generica

    tokens = _create_tokens_for_user(db, user)
    return {**tokens, "user": user}


@router.post("/google", response_model=TokenResponse)
async def google_auth(data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """RF-09: Login com Google OAuth2 (Authorization Code flow)."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google OAuth nao configurado")

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
        raise HTTPException(status_code=400, detail="Codigo Google invalido")

    google_data = token_response.json()
    id_token = google_data.get("id_token")

    # Decodificar ID token (sem verificacao de assinatura — ja validado pelo Google)
    from jose import jwt as jose_jwt
    user_info = jose_jwt.get_unverified_claims(id_token)

    google_id = user_info.get("sub")
    email = user_info.get("email")
    nome = user_info.get("name", "")
    avatar_url = user_info.get("picture")

    # Buscar usuario existente por google_id ou email (RN-017: merge)
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
            # Criar novo usuario via Google
            user = User(
                nome=nome,
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
                email_verified=True,  # Email verificado pelo Google
            )
            user = crud.create_user(db, user)

    tokens = _create_tokens_for_user(db, user)
    return {**tokens, "user": user}


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """RF-10: Renovar tokens via refresh token (com rotacao — RN-014)."""
    payload = verify_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token invalido")

    # Verificar se token existe no banco (nao foi revogado)
    token_hash = hash_token(data.refresh_token)
    stored_token = crud.get_refresh_token_by_hash(db, token_hash)
    if not stored_token or stored_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expirado ou revogado")

    # Rotacao: invalidar token antigo
    crud.delete_refresh_token(db, stored_token)

    # Gerar novo par de tokens
    user = crud.get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado")

    tokens = _create_tokens_for_user(db, user)
    return tokens


@router.post("/logout")
def logout(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RF-10: Logout — invalida refresh token no banco."""
    token_hash = hash_token(data.refresh_token)
    stored_token = crud.get_refresh_token_by_hash(db, token_hash)
    if stored_token:
        crud.delete_refresh_token(db, stored_token)
    return {"message": "Logout realizado com sucesso"}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """RF-11: Solicitar email de recuperacao de senha (RN-016)."""
    # Sempre retorna 200 por seguranca (nao revela se email existe)
    user = crud.get_user_by_email(db, data.email)
    if user and user.password_hash:
        # Gerar token de reset (JWT com 1h de expiracao)
        from jose import jwt as jose_jwt
        reset_token = jose_jwt.encode(
            {"sub": user.id, "type": "reset", "exp": datetime.utcnow() + timedelta(hours=1)},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        send_password_reset_email(user.email, reset_token, user.nome)

    return {"message": "Se o email estiver cadastrado, voce recebera um link de recuperacao"}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """RF-11: Redefinir senha com token de reset (RN-016)."""
    payload = verify_token(data.token)
    if not payload or payload.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Token de reset invalido ou expirado")

    user = crud.get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=400, detail="Token de reset invalido")

    user.password_hash = hash_password(data.new_password)
    crud.update_user(db, user)

    # Invalidar todos os refresh tokens do usuario (seguranca)
    crud.delete_user_refresh_tokens(db, user.id)

    return {"message": "Senha redefinida com sucesso"}
```

#### 2b.6 Validacoes

| Campo           | Regra                                          | Mensagem de Erro / Status                            |
|-----------------|-------------------------------------------------|------------------------------------------------------|
| email (register)| Deve ser unico no sistema                      | 409 "Email ja cadastrado" (RN-011)                   |
| password        | Minimo 6 caracteres                            | Validacao Pydantic Field(min_length=6)               |
| nome            | Obrigatorio, 1-255 chars                       | Validacao Pydantic Field                             |
| email/password (login) | Devem corresponder a usuario existente   | 401 "Credenciais invalidas" (generico)               |
| Google code     | Deve ser valido para troca por tokens          | 400 "Codigo Google invalido"                         |
| refresh_token   | Deve ser valido, nao expirado, existente no DB | 401 "Refresh token invalido"                         |
| reset token     | Deve ser valido e nao expirado (1h)            | 400 "Token de reset invalido ou expirado" (RN-016)   |

---

### Feature: [RF-12] Perfil de Usuario

#### 2b.1 Descricao Tecnica

Endpoints para visualizar e editar perfil do usuario autenticado, incluindo troca de senha.

#### 2b.2 Arquivos

| Acao  | Caminho                          | Descricao                               |
|-------|----------------------------------|-----------------------------------------|
| Criar | `backend/app/routers/users.py`  | 3 endpoints de perfil                    |

#### 2b.3 API Endpoints

**`backend/app/routers/users.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, hash_password, verify_password
from app.models import User
from app.schemas import UserResponse, UserUpdate, ChangePasswordRequest
from app import crud

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """RF-12: Visualizar perfil do usuario autenticado."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RF-12: Atualizar perfil (nome e/ou email)."""
    update_data = data.model_dump(exclude_unset=True)

    # Verificar unicidade do email se alterado
    if "email" in update_data and update_data["email"] != current_user.email:
        existing = crud.get_user_by_email(db, update_data["email"])
        if existing:
            raise HTTPException(status_code=409, detail="Email ja esta em uso")

    for field, value in update_data.items():
        setattr(current_user, field, value)

    return crud.update_user(db, current_user)


@router.patch("/me/password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RF-12: Trocar senha (RN-018: rejeita Google-only)."""
    if not current_user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="Usuario cadastrado via Google nao possui senha para alterar"  # RN-018
        )

    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    current_user.password_hash = hash_password(data.new_password)
    crud.update_user(db, current_user)

    return {"message": "Senha alterada com sucesso"}
```

#### 2b.4 Validacoes

| Campo            | Regra                                    | Mensagem de Erro / Status                                |
|------------------|------------------------------------------|----------------------------------------------------------|
| nome             | Opcional, 1-255 chars se fornecido       | Validacao Pydantic Field                                 |
| email            | Opcional, unico se alterado              | 409 "Email ja esta em uso"                               |
| current_password | Deve corresponder ao hash armazenado     | 400 "Senha atual incorreta"                              |
| new_password     | Minimo 6 caracteres                      | Validacao Pydantic Field(min_length=6)                   |
| Google-only user | Nao pode trocar senha                    | 400 "Usuario cadastrado via Google nao possui senha..." (RN-018) |

---

### Feature: [RF-08 a RF-12] Frontend Auth

#### 2b.1 Descricao Tecnica

Implementa o frontend de autenticacao completo: contexto de auth, paginas de login/registro/recuperacao/perfil, rotas protegidas e gerenciamento de tokens em localStorage.

#### 2b.2 Arquivos

| Acao  | Caminho                                          | Descricao                               |
|-------|--------------------------------------------------|-----------------------------------------|
| Criar | `frontend/src/contexts/AuthContext.tsx`          | AuthProvider: estado do usuario, tokens  |
| Criar | `frontend/src/hooks/useAuth.ts`                 | Hook de conveniencia                     |
| Criar | `frontend/src/services/authApi.ts`              | Funcoes de API de auth                   |
| Criar | `frontend/src/pages/LoginPage.tsx`              | Formulario login + Google                |
| Criar | `frontend/src/pages/RegisterPage.tsx`           | Formulario cadastro                      |
| Criar | `frontend/src/pages/ForgotPasswordPage.tsx`     | Input email recuperacao                  |
| Criar | `frontend/src/pages/ResetPasswordPage.tsx`      | Nova senha (token via query param)       |
| Criar | `frontend/src/pages/ProfilePage.tsx`            | Visualizar/editar perfil + trocar senha  |

#### 2b.3 Interfaces / Types

**Frontend — Types (`frontend/src/types.ts` — secao Auth, CR-002):**

```typescript
// ========== Auth Types (CR-002) ==========

export interface User {
  id: string;
  nome: string;
  email: string;
  avatar_url: string | null;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  nome: string;
  email: string;
  password: string;
}

export interface TokenResponse extends AuthTokens {
  user?: User;
}
```

#### 2b.4 Codigo

**`frontend/src/services/authApi.ts`**

```typescript
import type { TokenResponse, LoginCredentials, RegisterData, User } from "../types";

const BASE_URL = "/api";

async function authRequest<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export function loginUser(credentials: LoginCredentials): Promise<TokenResponse> {
  return authRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function registerUser(data: RegisterData): Promise<TokenResponse> {
  return authRequest<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function googleAuth(code: string): Promise<TokenResponse> {
  return authRequest<TokenResponse>("/auth/google", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export function refreshTokenApi(refreshToken: string): Promise<TokenResponse> {
  return authRequest<TokenResponse>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function logoutUser(refreshToken: string, accessToken: string): Promise<void> {
  return authRequest<void>("/auth/logout", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function forgotPassword(email: string): Promise<{ message: string }> {
  return authRequest<{ message: string }>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
  return authRequest<{ message: string }>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export function getProfile(accessToken: string): Promise<User> {
  return authRequest<User>("/users/me", {
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
  });
}

export function updateProfile(
  data: { nome?: string; email?: string },
  accessToken: string
): Promise<User> {
  return authRequest<User>("/users/me", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
    body: JSON.stringify(data),
  });
}

export function changePassword(
  currentPassword: string,
  newPassword: string,
  accessToken: string
): Promise<{ message: string }> {
  return authRequest<{ message: string }>("/users/me/password", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}
```

**`frontend/src/contexts/AuthContext.tsx`**

```typescript
import { createContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { jwtDecode } from "jwt-decode";
import type { User, LoginCredentials, RegisterData } from "../types";
import * as authApi from "../services/authApi";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  loginWithGoogle: (code: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;

  // Verificar tokens no mount
  useEffect(() => {
    const accessToken = localStorage.getItem("access_token");
    if (accessToken) {
      try {
        const decoded = jwtDecode<{ exp: number; sub: string }>(accessToken);
        if (decoded.exp * 1000 > Date.now()) {
          // Token valido — buscar perfil
          authApi.getProfile(accessToken).then(setUser).catch(() => {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
          });
        } else {
          // Token expirado — tentar refresh
          const refreshToken = localStorage.getItem("refresh_token");
          if (refreshToken) {
            authApi.refreshTokenApi(refreshToken).then((tokens) => {
              localStorage.setItem("access_token", tokens.access_token);
              localStorage.setItem("refresh_token", tokens.refresh_token);
              if (tokens.user) setUser(tokens.user);
              else authApi.getProfile(tokens.access_token).then(setUser);
            }).catch(() => {
              localStorage.removeItem("access_token");
              localStorage.removeItem("refresh_token");
            });
          }
        }
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const response = await authApi.loginUser(credentials);
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("refresh_token", response.refresh_token);
    if (response.user) setUser(response.user);
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    const response = await authApi.registerUser(data);
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("refresh_token", response.refresh_token);
    if (response.user) setUser(response.user);
  }, []);

  const loginWithGoogle = useCallback(async (code: string) => {
    const response = await authApi.googleAuth(code);
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("refresh_token", response.refresh_token);
    if (response.user) setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    const accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");
    if (accessToken && refreshToken) {
      try {
        await authApi.logoutUser(refreshToken, accessToken);
      } catch {
        // Ignorar erro — limpar tokens localmente de qualquer forma
      }
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  }, []);

  const updateUser = useCallback((updatedUser: User) => {
    setUser(updatedUser);
  }, []);

  return (
    <AuthContext.Provider value={{
      user, isAuthenticated, isLoading,
      login, register, loginWithGoogle, logout, updateUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
}
```

**`frontend/src/hooks/useAuth.ts`**

```typescript
import { useContext } from "react";
import { AuthContext } from "../contexts/AuthContext";

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
}
```

**Nota:** Os componentes de pagina (LoginPage, RegisterPage, ForgotPasswordPage, ResetPasswordPage, ProfilePage) seguem padrao de formulario simples com Tailwind CSS. Cada pagina usa `useAuth()` para funcoes de auth e `useNavigate()` para redirecionamento. Ver CR-002 tarefas CR-T-25 a CR-T-29 para detalhes de comportamento de cada pagina.

---

### Feature: Migration 002 (CR-002)

#### 2b.1 Descricao Tecnica

Migration Alembic que cria tabelas de autenticacao, limpa dados existentes (clean slate) e adiciona FK `user_id` nas tabelas existentes.

#### 2b.2 Arquivos

| Acao  | Caminho                                                    | Descricao                                              |
|-------|------------------------------------------------------------|--------------------------------------------------------|
| Criar | `backend/alembic/versions/002_add_users_and_auth.py`      | Criar users/refresh_tokens, limpar dados, add user_id  |

#### 2b.3 Codigo

```python
"""002: Add users and auth tables (CR-002)

Revision ID: 002
Revises: 001
Create Date: 2026-02-09
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Criar tabela users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True, unique=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # 2. Criar tabela refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # 3. Clean slate: apagar dados existentes (sem user_id nao podem ser associados)
    op.execute("DELETE FROM expenses")
    op.execute("DELETE FROM incomes")

    # 4. Remover indices antigos de mes_referencia
    op.drop_index("ix_expenses_mes_referencia", table_name="expenses")
    op.drop_index("ix_incomes_mes_referencia", table_name="incomes")

    # 5. Adicionar user_id FK em expenses e incomes
    op.add_column("expenses", sa.Column("user_id", sa.String(36),
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    op.add_column("incomes", sa.Column("user_id", sa.String(36),
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False))

    # 6. Criar indices compostos (user_id, mes_referencia)
    op.create_index("ix_expenses_user_month", "expenses", ["user_id", "mes_referencia"])
    op.create_index("ix_incomes_user_month", "incomes", ["user_id", "mes_referencia"])


def downgrade():
    op.drop_index("ix_incomes_user_month", table_name="incomes")
    op.drop_index("ix_expenses_user_month", table_name="expenses")
    op.drop_column("incomes", "user_id")
    op.drop_column("expenses", "user_id")
    op.create_index("ix_incomes_mes_referencia", "incomes", ["mes_referencia"])
    op.create_index("ix_expenses_mes_referencia", "expenses", ["mes_referencia"])
    op.drop_table("refresh_tokens")
    op.drop_table("users")
```

---

