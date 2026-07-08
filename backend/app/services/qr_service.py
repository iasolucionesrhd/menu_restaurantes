import io

import qrcode

from app.config import settings
from app.models.mesa import Mesa
from app.models.restaurante import Restaurante


def mesa_public_url(restaurante: Restaurante, mesa: Mesa) -> str:
    return f"{settings.FRONTEND_BASE_URL}/r/{restaurante.slug}/mesa/{mesa.codigo_qr}"


def generate_qr_png(data: str) -> bytes:
    img = qrcode.make(data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
