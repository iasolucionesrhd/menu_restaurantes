from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.restaurante import Restaurante
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, UsuarioOut
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(Usuario).where(Usuario.email == payload.email))
    usuario = result.scalar_one_or_none()

    if usuario is None or not verify_password(payload.password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")

    restaurante = await db.get(Restaurante, usuario.restaurante_id)

    token = create_access_token(sub=str(usuario.id), restaurante_id=usuario.restaurante_id, rol=usuario.rol.value)
    usuario_out = UsuarioOut(
        id=usuario.id,
        email=usuario.email,
        rol=usuario.rol,
        restaurante_id=usuario.restaurante_id,
        restaurante_slug=restaurante.slug,
    )
    return TokenResponse(access_token=token, usuario=usuario_out)
