import re

from pydantic import BaseModel, field_validator


class SucursalOut(BaseModel):
    id: int
    nombre: str
    slug: str

    model_config = {"from_attributes": True}


class SucursalCreate(BaseModel):
    nombre: str
    slug: str

    @field_validator("slug")
    @classmethod
    def slug_valido(cls, v: str) -> str:
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", v):
            raise ValueError("El slug solo puede tener minúsculas, números y guiones (ej. mi-sucursal-2)")
        return v


class RestauranteOut(BaseModel):
    id: int
    nombre: str
    slug: str
    tilopay_configurado: bool
    pin_cancelacion_configurado: bool

    model_config = {"from_attributes": True}


class RestauranteUpdate(BaseModel):
    nombre: str | None = None
    tilopay_llave_api: str | None = None
    tilopay_usuario_api: str | None = None
    tilopay_password_api: str | None = None
    pin_cancelacion: str | None = None
