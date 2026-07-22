from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_restaurante_id, get_current_usuario, get_owned_or_404, require_role
from app.enums import RolUsuario
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioAdminOut, UsuarioCreate
from app.security import hash_password

router = APIRouter(
    prefix="/api/admin/usuarios",
    tags=["admin:usuarios"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN))],
)


@router.get("", response_model=list[UsuarioAdminOut])
async def list_usuarios(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[Usuario]:
    result = await db.execute(select(Usuario).where(Usuario.restaurante_id == restaurante_id))
    return list(result.scalars().all())


@router.post("", response_model=UsuarioAdminOut, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    payload: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Usuario:
    usuario = Usuario(
        restaurante_id=restaurante_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol=payload.rol,
    )
    db.add(usuario)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese correo ya está en uso")
    await db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
    usuario_actual: Usuario = Depends(get_current_usuario),
) -> None:
    if usuario_id == usuario_actual.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes eliminar tu propia cuenta")
    usuario = await get_owned_or_404(db, Usuario, usuario_id, restaurante_id)
    await db.delete(usuario)
    await db.commit()
