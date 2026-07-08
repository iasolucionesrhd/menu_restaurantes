from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.enums import RolUsuario
from app.models.restaurante import Restaurante
from app.models.usuario import Usuario
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_usuario(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_error
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_error

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise credentials_error

    usuario = await db.get(Usuario, int(usuario_id))
    if usuario is None:
        raise credentials_error
    return usuario


def require_role(*roles: RolUsuario) -> Callable:
    async def dependency(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para esta acción")
        return usuario

    return dependency


async def get_current_restaurante_id(usuario: Usuario = Depends(get_current_usuario)) -> int:
    return usuario.restaurante_id


async def get_restaurante_by_slug(slug: str, db: AsyncSession = Depends(get_db)) -> Restaurante:
    result = await db.execute(select(Restaurante).where(Restaurante.slug == slug))
    restaurante = result.scalar_one_or_none()
    if restaurante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurante no encontrado")
    return restaurante


async def get_owned_or_404(db: AsyncSession, model, id_: int, restaurante_id: int):
    obj = await db.get(model, id_)
    if obj is None or obj.restaurante_id != restaurante_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    return obj
