from pydantic import BaseModel

from app.enums import RolUsuario


class LoginRequest(BaseModel):
    email: str
    password: str


class UsuarioOut(BaseModel):
    id: int
    email: str
    rol: RolUsuario
    restaurante_id: int
    restaurante_slug: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
