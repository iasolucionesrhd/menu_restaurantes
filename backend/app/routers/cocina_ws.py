import jwt
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_restaurante_by_slug
from app.enums import RolUsuario
from app.models.restaurante import Restaurante
from app.security import decode_access_token
from app.services.ws_manager import manager

router = APIRouter(tags=["ws:cocina"])


@router.websocket("/api/ws/cocina/{slug}")
async def cocina_websocket(
    websocket: WebSocket,
    restaurante: Restaurante = Depends(get_restaurante_by_slug),
    db: AsyncSession = Depends(get_db),
) -> None:
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        await websocket.close(code=4401)
        return

    if payload.get("rol") not in (RolUsuario.ADMIN.value, RolUsuario.COCINA.value):
        await websocket.close(code=4403)
        return
    if payload.get("restaurante_id") != restaurante.id:
        await websocket.close(code=4403)
        return

    await manager.connect(restaurante.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(restaurante.id, websocket)
