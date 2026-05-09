# detector.py
# Autora: Dana
# Detecta el tipo de archivo por extension y MIME type.
# Sin dependencias externas, solo stdlib.

import mimetypes
from pathlib import Path
from .exceptions import UnsupportedFile

# --- Categorias soportadas ---
# Cada extension mapea a una categoria que el extractor va a usar despues

_EXTENSIONES = {
    # Texto plano
    ".txt": "text", ".md": "text", ".rst": "text", ".log": "text",
    ".csv": "text", ".json": "text", ".xml": "text", ".yaml": "text",
    ".yml": "text", ".html": "text", ".htm": "text", ".toml": "text",
    ".ini": "text", ".cfg": "text",

    # Codigo fuente (40+ lenguajes)
    ".py": "code",   ".js": "code",  ".ts": "code",  ".jsx": "code",
    ".tsx": "code",  ".java": "code", ".c": "code",  ".cpp": "code",
    ".cc": "code",   ".h": "code",   ".cs": "code",  ".go": "code",
    ".rs": "code",   ".rb": "code",  ".php": "code", ".swift": "code",
    ".kt": "code",   ".scala": "code", ".r": "code", ".sh": "code",
    ".bash": "code", ".ps1": "code", ".sql": "code", ".dart": "code",
    ".lua": "code",  ".pl": "code",  ".ex": "code",  ".hs": "code",
    ".clj": "code",  ".erl": "code", ".proto": "code",

    # Audio
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".flac": "audio",
    ".aac": "audio", ".m4a": "audio", ".opus": "audio", ".aiff": "audio",
    ".amr": "audio",

    # Video
    ".mp4": "video", ".mkv": "video", ".avi": "video", ".mov": "video",
    ".wmv": "video", ".flv": "video", ".webm": "video", ".m4v": "video",
    ".mpeg": "video", ".mpg": "video", ".3gp": "video",

    # Imagen (incluye capturas de graficas)
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".gif": "image",
    ".bmp": "image", ".webp": "image", ".tiff": "image", ".tif": "image",
    ".heic": "image", ".heif": "image",

    # Documentos
    ".pdf": "document", ".docx": "document", ".doc": "document",
    ".odt": "document", ".rtf": "document",

    # Datos tabulares (graficas de datos)
    ".xlsx": "spreadsheet", ".xls": "spreadsheet",
}

# Lenguaje de programacion por extension (para mostrarselo a Claude)
_LENGUAJE = {
    ".py": "Python",     ".js": "JavaScript", ".ts": "TypeScript",
    ".java": "Java",     ".c": "C",           ".cpp": "C++",
    ".cs": "C#",         ".go": "Go",         ".rs": "Rust",
    ".rb": "Ruby",       ".php": "PHP",       ".swift": "Swift",
    ".kt": "Kotlin",     ".scala": "Scala",   ".r": "R",
    ".sh": "Shell",      ".bash": "Bash",     ".sql": "SQL",
    ".dart": "Dart",     ".lua": "Lua",       ".hs": "Haskell",
    ".clj": "Clojure",   ".erl": "Erlang",    ".ex": "Elixir",
    ".proto": "Protobuf",
}


def detectar(ruta: str) -> tuple[str, str, str]:
    """
    Detecta el tipo de un archivo.

    Parametros:
        ruta  -- ruta al archivo en disco

    Retorna:
        (categoria, mime_type, extra)
        - categoria : "text" | "code" | "audio" | "video" |
                      "image" | "document" | "spreadsheet" | "opengl"
        - mime_type : tipo MIME del archivo
        - extra     : lenguaje de programacion si es codigo, "" si no

    Errores:
        FileNotFoundError  -- si el archivo no existe
        UnsupportedFile    -- si la extension no esta soportada
    """
    p = Path(ruta)

    if not p.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    if not p.is_file():
        raise ValueError(f"La ruta no es un archivo: {ruta}")

    ext = p.suffix.lower()
    categoria = _EXTENSIONES.get(ext)

    # Si la extension no esta en el mapa, intentar con MIME de stdlib
    if categoria is None:
        mime, _ = mimetypes.guess_type(ruta)
        if mime:
            if mime.startswith("text/"):    categoria = "text"
            elif mime.startswith("audio/"): categoria = "audio"
            elif mime.startswith("video/"): categoria = "video"
            elif mime.startswith("image/"): categoria = "image"
            elif mime == "application/pdf": categoria = "document"

    if categoria is None:
        raise UnsupportedFile(
            f"Tipo de archivo no soportado: '{ext}'\n"
            f"Tipos aceptados: texto, codigo, audio, video, "
            f"imagen, PDF/DOCX, XLSX."
        )

    mime, _ = mimetypes.guess_type(ruta)
    mime = mime or "application/octet-stream"
    extra = _LENGUAJE.get(ext, "")

    return categoria, mime, extra


def es_grafica_opengl(datos: bytes) -> bool:
    """
    Verifica si unos bytes vienen de una captura OpenGL.
    Eddy va a usar esto desde su modulo opengl_capture.py.
    Devuelve True si parece una imagen PNG valida (lo que OpenGL genera).
    """
    # Los primeros 8 bytes de un PNG siempre son estos
    PNG_HEADER = b"\x89PNG\r\n\x1a\n"
    return datos[:8] == PNG_HEADER
