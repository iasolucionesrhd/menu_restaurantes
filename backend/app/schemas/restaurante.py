from pydantic import BaseModel


class RestauranteOut(BaseModel):
    id: int
    nombre: str
    slug: str
    tilopay_configurado: bool

    model_config = {"from_attributes": True}


class RestauranteUpdate(BaseModel):
    nombre: str | None = None
    tilopay_llave_api: str | None = None
    tilopay_usuario_api: str | None = None
    tilopay_password_api: str | None = None
