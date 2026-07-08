from decimal import Decimal

from pydantic import BaseModel


class ItemMenuOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    precio: Decimal
    imagen_url: str | None

    model_config = {"from_attributes": True}


class CategoriaMenuOut(BaseModel):
    id: int
    nombre: str
    items: list[ItemMenuOut]


class MenuPublicoOut(BaseModel):
    restaurante_nombre: str
    restaurante_slug: str
    payment_mode: str
    categorias: list[CategoriaMenuOut]


class MesaPublicaOut(BaseModel):
    numero: int | None
    tipo_entrega: str
