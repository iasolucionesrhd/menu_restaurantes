from decimal import Decimal

from pydantic import BaseModel

from app.schemas.modificador import ModificadorGrupoOut


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


class ItemIngredienteOut(BaseModel):
    ingrediente_id: int
    nombre: str
    unidad: str
    cantidad_requerida: Decimal


class ItemOut(BaseModel):
    id: int
    categoria_id: int
    nombre: str
    descripcion: str | None
    precio: Decimal
    disponible: bool
    imagen_url: str | None
    ingredientes: list[ItemIngredienteOut] = []
    modificador_grupos: list[ModificadorGrupoOut] = []

    model_config = {"from_attributes": True}


class ItemIngredienteIn(BaseModel):
    ingrediente_id: int
    cantidad_requerida: Decimal


class RecetaUpdate(BaseModel):
    ingredientes: list[ItemIngredienteIn]
