from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_restaurante_by_slug
from app.models.cliente import Cliente
from app.models.restaurante import Restaurante
from app.schemas.cliente import PerfilClienteOut, PerfilClienteRequest
from app.services.google_auth import verify_google_id_token

router = APIRouter(prefix="/api/public/{slug}", tags=["public:clientes"])


@router.post("/cliente/perfil", response_model=PerfilClienteOut)
async def obtener_perfil_cliente(
    payload: PerfilClienteRequest,
    restaurante: Restaurante = Depends(get_restaurante_by_slug),
    db: AsyncSession = Depends(get_db),
) -> PerfilClienteOut:
    google_info = await verify_google_id_token(payload.google_id_token)

    result = await db.execute(
        select(Cliente).where(
            Cliente.restaurante_id == restaurante.id,
            Cliente.google_sub == google_info.sub,
        )
    )
    cliente = result.scalar_one_or_none()
    # 404 solo si no existe la fila Cliente. Un cliente que ya pidió antes
    # pero nunca marcó "necesito factura" sí existe: debe dar 200 con los
    # campos factura_* en None, no 404.
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay perfil guardado")

    return PerfilClienteOut(
        nombre=cliente.nombre,
        correo=cliente.correo,
        telefono=cliente.telefono,
        factura_nombre=cliente.factura_nombre,
        factura_cedula=cliente.factura_cedula,
        factura_correo=cliente.factura_correo,
        factura_telefono=cliente.factura_telefono,
        factura_direccion=cliente.factura_direccion,
        factura_actividad_economica=cliente.factura_actividad_economica,
    )
