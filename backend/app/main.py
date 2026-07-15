from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    auth,
    categorias,
    clientes_publico,
    cocina_ws,
    items,
    menu_publico,
    mesas,
    pagos,
    pedidos,
    restaurantes,
)

app = FastAPI(title="Menú Digital QR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(restaurantes.router)
app.include_router(categorias.router)
app.include_router(items.router)
app.include_router(mesas.router)
app.include_router(menu_publico.router)
app.include_router(clientes_publico.router)
app.include_router(pagos.router)
app.include_router(pedidos.public_router)
app.include_router(pedidos.staff_router)
app.include_router(cocina_ws.router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
