from pydantic import BaseModel

from app.enums import RolUsuario


class UsuarioCreate(BaseModel):
    email: str
    password: str
    rol: RolUsuario


class UsuarioAdminOut(BaseModel):
    id: int
    email: str
    rol: RolUsuario

    model_config = {"from_attributes": True}
