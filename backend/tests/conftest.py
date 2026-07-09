import re
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app import models  # noqa: F401  (populates Base.metadata)
from app.config import settings
from app.database import Base, get_db
from app.enums import RolUsuario
from app.main import app
from app.models.categoria import Categoria
from app.models.item import Item
from app.models.mesa import Mesa
from app.models.restaurante import Restaurante
from app.models.usuario import Usuario
from app.security import hash_password

TEST_DATABASE_URL = re.sub(r"/[^/]+$", "/menu_test", settings.DATABASE_URL)

# NullPool: cada checkout abre una conexión asyncpg nueva y la cierra al
# terminar. Necesario porque las fixtures de sesión y de función corren en
# event loops distintos, y una conexión asyncpg no puede reutilizarse entre
# loops diferentes (causa "another operation is in progress").
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def _create_schema():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def make_restaurante():
    async def _make(db: AsyncSession, *, nombre: str = "Pizzería Luna", slug: str = "pizzeria-luna") -> Restaurante:
        restaurante = Restaurante(nombre=nombre, slug=slug)
        db.add(restaurante)
        await db.commit()
        await db.refresh(restaurante)
        return restaurante

    return _make


@pytest.fixture
def make_usuario():
    async def _make(
        db: AsyncSession,
        *,
        restaurante: Restaurante,
        email: str = "admin@demo.test",
        password: str = "clave123",
        rol: RolUsuario = RolUsuario.ADMIN,
    ) -> Usuario:
        usuario = Usuario(
            restaurante_id=restaurante.id,
            email=email,
            password_hash=hash_password(password),
            rol=rol,
        )
        db.add(usuario)
        await db.commit()
        await db.refresh(usuario)
        return usuario

    return _make


@pytest.fixture
def make_categoria():
    async def _make(db: AsyncSession, *, restaurante: Restaurante, nombre: str = "Pizzas", orden: int = 0) -> Categoria:
        categoria = Categoria(restaurante_id=restaurante.id, nombre=nombre, orden=orden)
        db.add(categoria)
        await db.commit()
        await db.refresh(categoria)
        return categoria

    return _make


@pytest.fixture
def make_item():
    async def _make(
        db: AsyncSession,
        *,
        restaurante: Restaurante,
        categoria: Categoria,
        nombre: str = "Pizza Margarita",
        precio: str = "10.00",
        disponible: bool = True,
    ) -> Item:
        item = Item(
            restaurante_id=restaurante.id,
            categoria_id=categoria.id,
            nombre=nombre,
            precio=precio,
            disponible=disponible,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    return _make


@pytest.fixture
def make_mesa():
    async def _make(
        db: AsyncSession, *, restaurante: Restaurante, numero: int | None = 1, codigo_qr: str = "qr-mesa-1"
    ) -> Mesa:
        mesa = Mesa(restaurante_id=restaurante.id, numero=numero, codigo_qr=codigo_qr)
        db.add(mesa)
        await db.commit()
        await db.refresh(mesa)
        return mesa

    return _make
