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
