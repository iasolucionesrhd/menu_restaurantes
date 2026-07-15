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


async def verify_google_id_token(token: str) -> GoogleUserInfo:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google sign-in no está configurado")

    try:
        # get_signing_key_from_jwt hace una llamada de red bloqueante en
        # cache-miss (rotación de claves) — se corre en un thread aparte
        # para no trabar el event loop.
        signing_key = await asyncio.to_thread(_jwks_client.get_signing_key_from_jwt, token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],  # whitelist explícita: defensa contra ataques de confusión de algoritmo
            audience=settings.GOOGLE_CLIENT_ID,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No se pudo verificar el token de Google"
        ) from exc

    if payload.get("iss") not in _GOOGLE_ISSUERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido")

    return GoogleUserInfo(sub=payload["sub"], email=payload.get("email"), nombre=payload.get("name"))
