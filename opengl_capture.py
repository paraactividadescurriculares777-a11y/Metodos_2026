"""
opengl_capture.py
-----------------
Captura un frame de una superficie OpenGL/pygame y lo convierte
a un string base64 de PNG listo para enviar a la API de Claude.

Contrato público:
    capture_opengl(surface) -> str   # base64 PNG

Autor: Eddy
Rama:  feat/opengl-input
"""

from __future__ import annotations

import base64
import io
import logging
from typing import TYPE_CHECKING

try:
    import pygame
except ImportError:
    pygame = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Excepción propia — evita exponer dependencias internas al caller
# ---------------------------------------------------------------------------

class CaptureError(Exception):
    """Se lanza cuando no es posible capturar el frame."""


# ---------------------------------------------------------------------------
# Función pública principal
# ---------------------------------------------------------------------------

def capture_opengl(surface: "pygame.Surface") -> str:
    """
    Captura un frame de una superficie pygame/OpenGL y devuelve
    el PNG codificado en base64 como string.

    Parameters
    ----------
    surface:
        Superficie pygame activa. Debe ser el display surface
        obtenido con pygame.display.set_mode(..., pygame.OPENGL).

    Returns
    -------
    str
        String base64 del PNG, listo para incluir en un payload JSON
        o en el campo ``source.data`` de la API de Claude.

    Raises
    ------
    CaptureError
        Si la superficie es None, tiene dimensiones inválidas,
        o falla la conversión.
    """
    _validate_surface(surface)

    try:
        png_bytes = _surface_to_png_bytes(surface)
        return _encode_base64(png_bytes)
    except CaptureError:
        raise
    except Exception as exc:  # pragma: no cover — errores inesperados de pygame
        logger.exception("Error inesperado al capturar el frame")
        raise CaptureError(f"No se pudo capturar el frame: {exc}") from exc


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _validate_surface(surface: object) -> None:
    """Valida que la superficie sea usable antes de intentar capturar."""
    if surface is None:
        raise CaptureError("La superficie es None. Inicializa pygame antes de capturar.")

    # pygame.Surface expone .get_size(); lo comprobamos duck-typing
    if not hasattr(surface, "get_size"):
        raise CaptureError(
            f"Se esperaba una pygame.Surface, se recibió {type(surface).__name__}."
        )

    width, height = surface.get_size()
    if width <= 0 or height <= 0:
        raise CaptureError(
            f"Dimensiones inválidas: {width}x{height}. "
            "La superficie debe tener ancho y alto mayores a 0."
        )


def _surface_to_png_bytes(surface: "pygame.Surface") -> bytes:
    """
    Convierte una pygame.Surface a bytes PNG en memoria.

    Usa io.BytesIO para no tocar el disco — más rápido y sin efectos
    secundarios en el sistema de archivos.
    """
    if pygame is None:
        raise CaptureError(
            "pygame no está instalado. Ejecuta: pip install pygame"
        )

    buffer = io.BytesIO()

    try:
        pygame.image.save(surface, buffer, "PNG")
    except pygame.error as exc:
        raise CaptureError(f"pygame no pudo guardar la imagen: {exc}") from exc

    buffer.seek(0)
    png_bytes = buffer.read()

    if not png_bytes:
        raise CaptureError("La conversión PNG produjo un buffer vacío.")

    return png_bytes


def _encode_base64(data: bytes) -> str:
    """Codifica bytes en base64 y devuelve un str limpio (sin saltos de línea)."""
    return base64.b64encode(data).decode("ascii")
