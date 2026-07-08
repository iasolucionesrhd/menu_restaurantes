import jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


async def test_login_success_issues_valid_jwt(client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario):
    restaurante = await make_restaurante(db)
    usuario = await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123")

    response = await client.post("/api/auth/login", json={"email": "admin@demo.test", "password": "clave123"})

    assert response.status_code == 200
    body = response.json()
    assert body["usuario"]["email"] == "admin@demo.test"
    assert body["usuario"]["restaurante_id"] == restaurante.id

    payload = jwt.decode(body["access_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == str(usuario.id)
    assert payload["restaurante_id"] == restaurante.id
    assert payload["rol"] == "admin"


async def test_login_wrong_password_returns_401(client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123")

    response = await client.post("/api/auth/login", json={"email": "admin@demo.test", "password": "incorrecta"})

    assert response.status_code == 401


async def test_login_unknown_email_returns_401(client: AsyncClient, db: AsyncSession):
    response = await client.post("/api/auth/login", json={"email": "nadie@demo.test", "password": "x"})
    assert response.status_code == 401
