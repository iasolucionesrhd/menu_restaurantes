from decimal import Decimal

from pydantic import BaseModel


class ModificadorCreate(BaseModel):
    nombre: str
    precio_extra: Decimal = Decimal("0")


class ModificadorUpdate(BaseModel):
    nombre: str | None = None
    precio_extra: Decimal | None = None


class ModificadorOut(BaseModel):
    id: int
    nombre: str
    precio_extra: Decimal

    model_config = {"from_attributes": True}


class ModificadorGrupoCreate(BaseModel):
    nombre: str
    obligatorio: bool = False
    seleccion_multiple: bool = False


class ModificadorGrupoUpdate(BaseModel):
    nombre: str | None = None
    obligatorio: bool | None = None
    seleccion_multiple: bool | None = None


class ModificadorGrupoOut(BaseModel):
    id: int
    nombre: str
    obligatorio: bool
    seleccion_multiple: bool
    modificadores: list[ModificadorOut] = []

    model_config = {"from_attributes": True}
