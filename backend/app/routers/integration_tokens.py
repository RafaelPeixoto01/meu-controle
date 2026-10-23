"""CR-058: Gestao dos tokens de integracao do Lumi no Perfil (RF-22, RN-054).

Rotas do app (JWT do login): gerar, listar e revogar. O token aparece uma vez so,
na criacao; o banco guarda o hash e o prefixo.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.auth import generate_integration_token, get_current_user
from app.database import get_db
from app.models import IntegrationToken, User, utc_now
from app.schemas import IntegrationTokenCreate, IntegrationTokenCreated, IntegrationTokenResponse

router = APIRouter(prefix="/api/integration-tokens", tags=["integration-tokens"])

MAX_ACTIVE_TOKENS = 5


@router.get("", response_model=list[IntegrationTokenResponse])
def list_integration_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tokens ativos do usuario, do mais novo para o mais antigo (sem o token)."""
    return crud.get_active_integration_tokens(db, current_user.id)


@router.post("", response_model=IntegrationTokenCreated, status_code=201)
def create_integration_token(
    data: IntegrationTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gera um token: a resposta e a unica vez em que ele aparece."""
    if crud.count_active_integration_tokens(db, current_user.id) >= MAX_ACTIVE_TOKENS:
        raise HTTPException(
            status_code=409, detail=f"Limite de {MAX_ACTIVE_TOKENS} tokens ativos"
        )
    token, prefix, token_hash = generate_integration_token()
    row = crud.create_integration_token(
        db,
        IntegrationToken(
            user_id=current_user.id, name=data.name, prefix=prefix, token_hash=token_hash
        ),
    )
    return {**IntegrationTokenResponse.model_validate(row).model_dump(), "token": token}


@router.delete("/{token_id}", status_code=204)
def revoke_integration_token(
    token_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoga um token ativo do usuario: deixa de valer na hora."""
    row = crud.get_active_integration_token(db, token_id, current_user.id)
    if row is None:
        raise HTTPException(status_code=404, detail="Token não encontrado")
    row.revoked_at = utc_now()
    db.commit()
