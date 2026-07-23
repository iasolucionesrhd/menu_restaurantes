from decimal import Decimal

from pydantic import BaseModel

from app.enums import RolUsuario


class ModificadorEventoOut(BaseModel):
    nombre: str
    precio_extra: Decimal

    model_config = {"from_attributes": True}


class ModificadorGrupoEventoOut(BaseModel):
    nombre: str
    obligatorio: bool
    seleccion_multiple: bool
    modificadores: list[ModificadorEventoOut]

    model_config = {"from_attributes": True}


class ItemEventoOut(BaseModel):
    nombre: str
    descripcion: str | None
    precio: Decimal
    disponible: bool
    imagen_url: str | None
    modificador_grupos: list[ModificadorGrupoEventoOut]

    model_config = {"from_attributes": True}


class CategoriaEventoOut(BaseModel):
    nombre: str
    orden: int
    items: list[ItemEventoOut]

    model_config = {"from_attributes": True}


class MesaEventoOut(BaseModel):
    numero: int | None
    codigo_qr: str

    model_config = {"from_attributes": True}


class UsuarioEventoOut(BaseModel):
    email: str
    password_hash: str
    rol: RolUsuario

    model_config = {"from_attributes": True}


class RestauranteEventoOut(BaseModel):
    nombre: str
    slug: str
    pin_cancelacion_hash: str | None
    # Cifradas por instancia (Fernet): el ORM ya las entrega en texto plano al
    # leerlas de la nube; al asignarlas en el modelo del nodo destino se
    # vuelven a cifrar solas con el FERNET_KEY propio de ese nodo.
    tilopay_llave_api: str | None
    tilopay_usuario_api: str | None
    tilopay_password_api: str | None

    model_config = {"from_attributes": True}


class ExportacionEventoOut(BaseModel):
    restaurante: RestauranteEventoOut
    categorias: list[CategoriaEventoOut]
    mesas: list[MesaEventoOut]
    usuarios: list[UsuarioEventoOut]
