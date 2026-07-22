from decimal import Decimal

from pydantic import BaseModel, computed_field


class IngredienteCreate(BaseModel):
    nombre: str
    unidad: str
    stock_actual: Decimal = Decimal("0")
    stock_minimo: Decimal = Decimal("0")


class IngredienteUpdate(BaseModel):
    nombre: str | None = None
    unidad: str | None = None
    stock_actual: Decimal | None = None
    stock_minimo: Decimal | None = None


class IngredienteOut(BaseModel):
    id: int
    nombre: str
    unidad: str
    stock_actual: Decimal
    stock_minimo: Decimal

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def stock_bajo(self) -> bool:
        return self.stock_actual <= self.stock_minimo
