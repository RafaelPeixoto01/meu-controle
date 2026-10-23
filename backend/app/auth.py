import os
import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.models import utc_now

# Configuração
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY não definido. "
        "Defina a variável de ambiente SECRET_KEY antes de iniciar a aplicação."
    )
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
    """Cria JWT access token com expiração de 15 minutos (RN-013)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Cria JWT refresh token com expiração de 7 dias (RN-013)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Decodifica e valida um JWT. Retorna payload ou None se inválido."""
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
    FastAPI dependency: extrai usuário do JWT access token.
    Usado como Depends(get_current_user) nos endpoints protegidos.
    Retorna instância User ou lança HTTPException 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
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


# ========== Token de integracao (CR-058, RN-054, ADR-023) ==========

INTEGRATION_TOKEN_PREFIX = "mc_"
LAST_USED_EVERY = timedelta(minutes=1)  # last_used_at gravado no maximo uma vez por minuto
integration_scheme = HTTPBearer(auto_error=False)


def generate_integration_token() -> tuple[str, str, str]:
    """Novo token de integracao: (token, prefixo para a lista, hash SHA-256). So o hash e gravado."""
    secret = secrets.token_urlsafe(32)
    token = INTEGRATION_TOKEN_PREFIX + secret
    return token, secret[:8], hash_token(token)


def get_integration_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(integration_scheme),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency das rotas /api/integration/v1: so aceita o token de integracao
    (o JWT do login e recusado aqui, e o token nao passa no get_current_user).
    """
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de integração inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not credentials.credentials.startswith(INTEGRATION_TOKEN_PREFIX):
        raise invalid

    token = crud.get_integration_token_by_hash(db, hash_token(credentials.credentials))
    if token is None:
        raise invalid
    user = crud.get_user_by_id(db, token.user_id)
    if user is None:
        raise invalid

    now = utc_now()
    if token.last_used_at is None or now - token.last_used_at >= LAST_USED_EVERY:
        token.last_used_at = now
        db.commit()
    return user
