from pydantic import BaseModel


class MesaCreate(BaseModel):
    numero: int | None = None


class MesaOut(BaseModel):
    id: int
    numero: int | None
    codigo_qr: str

    model_config = {"from_attributes": True}
