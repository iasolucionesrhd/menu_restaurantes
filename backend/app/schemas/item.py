from decimal import Decimal

from pydantic import BaseModel


class ItemCreate(BaseModel):
    categoria_id: int
    nombre: str
    descripcion: str | None = None
    precio: Decimal
    disponible: bool = True
    imagen_url: str | None = None


class ItemUpdate(BaseModel):
    categoria_id: int | None = None
    nombre: str | None = None
    descripcion: str | None = None
    precio: Decimal | None = None
    disponible: bool | None = None
    imagen_url: str | None = None


class ItemOut(BaseModel):
    id: int
    categoria_id: int
    nombre: str
    descripcion: str | None
    precio: Decimal
    disponible: bool
    imagen_url: str | None

    model_config = {"from_attributes": True}
