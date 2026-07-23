from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/menu_digital"

    JWT_SECRET_KEY: str = "change-me-dev-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 12

    # Sin valor por defecto a propósito: debe generarse por instancia y vivir
    # solo en .env (ver .env.example), nunca en el código fuente.
    FERNET_KEY: str

    PAYMENT_MODE: str = "stub"
    TILOPAY_API_BASE_URL: str = "https://sandbox-api.tilopay.com"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # Client ID público de Google OAuth (no es secreto, es seguro dejarlo sin
    # configurar: el Sign-In con Google simplemente no se activa en ese caso).
    GOOGLE_CLIENT_ID: str | None = None

    SEED_ADMIN_PASSWORD: str = "devpassword123"

    # True solo en un nodo de evento local (ver scripts/importar_evento.py):
    # habilita el script de importación y, más adelante, la sincronización de
    # cierres de caja hacia la nube.
    MODO_NODO_EVENTO: bool = False


settings = Settings()
