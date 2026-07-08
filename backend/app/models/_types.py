from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app.security import decrypt_str, encrypt_str


class EncryptedString(TypeDecorator):
    """Almacena el valor cifrado con Fernet; expone texto plano en Python."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return encrypt_str(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return decrypt_str(value)
