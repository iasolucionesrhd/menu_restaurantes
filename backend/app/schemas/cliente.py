from pydantic import BaseModel


class PerfilClienteRequest(BaseModel):
    google_id_token: str


class PerfilClienteOut(BaseModel):
    nombre: str
    correo: str | None
    telefono: str | None
    factura_nombre: str | None
    factura_cedula: str | None
    factura_correo: str | None
    factura_telefono: str | None
    factura_direccion: str | None
    factura_actividad_economica: str | None
