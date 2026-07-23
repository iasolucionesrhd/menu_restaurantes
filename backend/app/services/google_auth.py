import asyncio

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.config import settings

_GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
# Instanciado una sola vez a nivel de módulo para que el cache de claves
# persista entre requests. Verificación completamente separada del JWT de
# staff (backend/app/security.py, HS256 con JWT_SECRET_KEY) — no compartir
# key material ni lógica entre ambas.
_jwks_client = jwt.PyJWKClient(_GOOGLE_JWKS_URL, lifespan=3600)


class GoogleUserInfo(BaseModel):
    sub: str
    email: str | None
    nombre: str | None


class GoogleAuthUnavailable(Exception):
    """No se pudo contactar a Google (sin conectividad) — distinto de que el
    token en sí sea inválido. Quien llama puede optar por degradar a invitado
    en vez de rechazar el pedido completo."""


async def verify_google_id_token(token: str) -> GoogleUserInfo:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google sign-in no está configurado")

    try:
        # get_signing_key_from_jwt hace una llamada de red bloqueante en
        # cache-miss (rotación de claves) — se corre en un thread aparte
        # para no trabar el event loop. Cualquier falla que no sea del propio
        # token (red caída, DNS, timeout) se distingue como "no disponible".
        signing_key = await asyncio.to_thread(_jwks_client.get_signing_key_from_jwt, token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido") from exc
    except Exception as exc:
        raise GoogleAuthUnavailable("No se pudo contactar a Google") from exc

    try:
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],  # whitelist explícita: defensa contra ataques de confusión de algoritmo
            audience=settings.GOOGLE_CLIENT_ID,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido") from exc

    if payload.get("iss") not in _GOOGLE_ISSUERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido")

    return GoogleUserInfo(sub=payload["sub"], email=payload.get("email"), nombre=payload.get("name"))
