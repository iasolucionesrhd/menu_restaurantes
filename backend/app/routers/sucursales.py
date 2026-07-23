from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_restaurante_id, get_current_usuario, require_role
from app.enums import RolUsuario
from app.models.categoria import Categoria
from app.models.item import Item
from app.models.mesa import Mesa
from app.models.modificador_grupo import ModificadorGrupo
from app.models.restaurante import Restaurante
from app.models.usuario import Usuario
from app.models.usuario_restaurante import UsuarioRestaurante
from app.schemas.auth import CambiarRestauranteRequest, TokenResponse, UsuarioOut
from app.schemas.evento import (
    CategoriaEventoOut,
    ExportacionEventoOut,
    MesaEventoOut,
    RestauranteEventoOut,
    UsuarioEventoOut,
)
from app.schemas.restaurante import SucursalCreate, SucursalOut
from app.security import create_access_token

auth_router = APIRouter(prefix="/api/auth", tags=["auth:sucursales"])
admin_router = APIRouter(
    prefix="/api/admin/sucursales",
    tags=["admin:sucursales"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN))],
)


async def _restaurantes_accesibles(db: AsyncSession, usuario: Usuario) -> list[int]:
    result = await db.execute(
        select(UsuarioRestaurante.restaurante_id).where(UsuarioRestaurante.usuario_id == usuario.id)
    )
    return [usuario.restaurante_id, *result.scalars().all()]


@auth_router.get("/mis-restaurantes", response_model=list[SucursalOut])
async def listar_mis_restaurantes(
    usuario: Usuario = Depends(get_current_usuario),
    db: AsyncSession = Depends(get_db),
) -> list[Restaurante]:
    ids = await _restaurantes_accesibles(db, usuario)
    result = await db.execute(select(Restaurante).where(Restaurante.id.in_(ids)))
    return list(result.scalars().all())


@auth_router.post("/cambiar-restaurante", response_model=TokenResponse)
async def cambiar_restaurante(
    payload: CambiarRestauranteRequest,
    usuario: Usuario = Depends(get_current_usuario),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    ids_permitidos = await _restaurantes_accesibles(db, usuario)
    if payload.restaurante_id not in ids_permitidos:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a esa sucursal")

    restaurante = await db.get(Restaurante, payload.restaurante_id)
    if restaurante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sucursal no encontrada")

    token = create_access_token(sub=str(usuario.id), restaurante_id=restaurante.id, rol=usuario.rol.value)
    usuario_out = UsuarioOut(
        id=usuario.id,
        email=usuario.email,
        rol=usuario.rol,
        restaurante_id=restaurante.id,
        restaurante_slug=restaurante.slug,
    )
    return TokenResponse(access_token=token, usuario=usuario_out)


@admin_router.post("", response_model=SucursalOut, status_code=status.HTTP_201_CREATED)
async def crear_sucursal(
    payload: SucursalCreate,
    usuario: Usuario = Depends(get_current_usuario),
    db: AsyncSession = Depends(get_db),
) -> Restaurante:
    restaurante = Restaurante(nombre=payload.nombre, slug=payload.slug)
    db.add(restaurante)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese slug ya está en uso")

    db.add(UsuarioRestaurante(usuario_id=usuario.id, restaurante_id=restaurante.id))
    await db.commit()
    await db.refresh(restaurante)
    return restaurante


@admin_router.get("/exportar-datos-evento", response_model=ExportacionEventoOut)
async def exportar_datos_evento(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> ExportacionEventoOut:
    """Foto completa de la sucursal activa (menú, mesas, staff, credenciales
    de pago) lista para cargarse en un nodo de evento nuevo con
    scripts/importar_evento.py."""
    restaurante = await db.get(Restaurante, restaurante_id)
    if restaurante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sucursal no encontrada")

    categorias_result = await db.execute(
        select(Categoria)
        .where(Categoria.restaurante_id == restaurante_id)
        .options(
            selectinload(Categoria.items)
            .selectinload(Item.modificador_grupos)
            .selectinload(ModificadorGrupo.modificadores)
        )
        .order_by(Categoria.orden)
    )
    categorias = categorias_result.scalars().all()

    mesas_result = await db.execute(select(Mesa).where(Mesa.restaurante_id == restaurante_id))
    mesas = mesas_result.scalars().all()

    usuarios_result = await db.execute(select(Usuario).where(Usuario.restaurante_id == restaurante_id))
    usuarios = usuarios_result.scalars().all()

    return ExportacionEventoOut(
        restaurante=RestauranteEventoOut.model_validate(restaurante),
        categorias=[CategoriaEventoOut.model_validate(c) for c in categorias],
        mesas=[MesaEventoOut.model_validate(m) for m in mesas],
        usuarios=[UsuarioEventoOut.model_validate(u) for u in usuarios],
    )
