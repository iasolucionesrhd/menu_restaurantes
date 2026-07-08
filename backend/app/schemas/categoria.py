from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    nombre: str
    orden: int = 0


class CategoriaUpdate(BaseModel):
    nombre: str | None = None
    orden: int | None = None


class CategoriaOut(BaseModel):
    id: int
    nombre: str
    orden: int

    model_config = {"from_attributes": True}
