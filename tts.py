# tts.py
# Autor: (Carlos)
# Modulo Text-to-Speech.
# Soporta multiples motores offline/online (incluyendo OpenAI y ElevenLabs) y divide textos largos.

import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

#Excepcion personalizada (debe estar en exceptions.py)
try:
    from .exceptions import TTSError
except ImportError:
    class TTSError(Exception):
        """Error relacionado con sintesis de voz."""
        pass

# ---------- Utilidad para dividir texto largo ----------
def _split_text(texto: str, limite_caracteres: int = 500) -> List[str]:
    """
    Divide un texto largo en fragmentos que no excedan limite_caracteres.
    Similar al metodo de TTSProcessor, pero como funcion independiente.
    """
    if not texto:
        return []
    palabras = texto.split()
    fragmentos = []
    fragmento_actual = ""

    for palabra in palabras:
        if len(fragmento_actual) + len(palabra) + 1 <= limite_caracteres:
            fragmento_actual += palabra + " "
        else:
            fragmentos.append(fragmento_actual.strip())
            fragmento_actual = palabra + " "
    if fragmento_actual:
        fragmentos.append(fragmento_actual.strip())
    return fragmentos

# ---------- Motores TTS ----------
def _con_openai(texto: str, voz: str = "alloy") -> Optional[tuple]:
    """Motor online usando la API de OpenAI."""
    try:
        import os
        from openai import OpenAI
        
        # Requiere que la variable de entorno OPENAI_API_KEY este configurada
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
            
        client = OpenAI(api_key=api_key)
        response = client.audio.speech.create(
            model="tts-1",
            voice=voz,
            input=texto
        )
        duracion = max(1.0, len(texto.split()) / 2.5)
        return response.content, "mp3", duracion
    except Exception:
        return None

def _con_elevenlabs(texto: str, voz_id: str = "JBFqnCBsd6RMkjVDRZzb") -> Optional[tuple]:
    """Motor online usando la API de ElevenLabs."""
    try:
        import os
        from elevenlabs.client import ElevenLabs
        
        # Requiere la variable ELEVENLABS_API_KEY
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            return None
            
        client = ElevenLabs(api_key=api_key)
        audio_generator = client.generate(
            text=texto,
            voice=voz_id,
            model="eleven_multilingual_v2"
        )
        # ElevenLabs devuelve un generador, lo convertimos a bytes
        audio_bytes = b"".join(audio_generator)
        duracion = max(1.0, len(texto.split()) / 2.5)
        return audio_bytes, "mp3", duracion
    except Exception:
        return None

def _con_pyttsx3(texto: str, velocidad: int = 150) -> Optional[tuple]:
    """Motor offline usando pyttsx3 (multiplataforma)."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', velocidad)
        # Guardar en archivo temporal
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = Path(f.name)
        engine.save_to_file(texto, str(tmp))
        engine.runAndWait()
        audio_bytes = tmp.read_bytes()
        tmp.unlink()
        duracion_estimada = max(1.0, len(texto.split()) / 3.5)
        return audio_bytes, "wav", duracion_estimada
    except Exception:
        return None

def _con_gtts(texto: str, idioma: str = "es") -> Optional[tuple]:
    """Motor online usando gTTS (requiere internet)."""
    try:
        from gtts import gTTS
        import io
        tts = gTTS(text=texto, lang=idioma, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        duracion = max(1.0, len(texto.split()) / 2.5)
        return buf.getvalue(), "mp3", duracion
    except Exception:
        return None

def _con_espeak(texto: str, velocidad: int = 150) -> Optional[tuple]:
    """Motor mediante comando espeak (Linux/Mac, requiere espeak instalado)."""
    import subprocess
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = Path(f.name)
        subprocess.run(
            ["espeak", "-w", str(tmp), "-s", str(velocidad), texto],
            check=True, capture_output=True
        )
        audio_bytes = tmp.read_bytes()
        tmp.unlink()
        duracion = max(1.0, len(texto.split()) / 3.0)
        return audio_bytes, "wav", duracion
    except (subprocess.SubprocessError, FileNotFoundError):
        return None
# ---------- Funcion principal ----------
def sintetizar(
    texto: str,
    cfg: Optional[Any] = None,
    motor: str = "auto",
    idioma: str = "es",
    velocidad: int = 150,
    limite_fragmento: int = 500,
    guardar_como: Optional[Path] = None,
    devolver_bytes: bool = True
) -> Dict[str, Any]:
    """
    Convierte texto a voz, dividiendolo en fragmentos si es necesario.
    Parametros:
        texto              -- texto a sintetizar (puede ser muy largo)
        cfg                -- configuracion global (reservado)
        motor              -- "auto", "openai", "elevenlabs", "pyttsx3", "gtts", "espeak"
        idioma             -- codigo de idioma (solo para gTTS)
        velocidad          -- palabras por minuto (solo offline)
        limite_fragmento   -- maximo caracteres por fragmento (recomendado 500)
        guardar_como       -- si se indica, guarda el archivo completo en esa ruta
        devolver_bytes     -- si True, incluye los bytes del audio en el resultado

    Retorna:
        {
            "exito": bool,
            "motor_usado": str,
            "audio_bytes": bytes | None,
            "archivo": Path | None,
            "formato": str,
            "duracion_seg": float,
            "fragmentos": int
        }
    Errores:
        TTSError si ningun motor funciona o texto vacio.
    """
    if not texto or not texto.strip():
        raise TTSError("El texto a sintetizar esta vacio")

    # Dividir el texto en fragmentos manejables
    fragmentos = _split_text(texto, limite_fragmento)
    if not fragmentos:
        raise TTSError("No se pudo dividir el texto en fragmentos")

    # Determinar orden de motores (Añadidos openai y elevenlabs al inicio)
    orden = ["openai", "elevenlabs", "pyttsx3", "gtts", "espeak"] if motor == "auto" else [motor]
    audio_final = b""
    formato_final = ""
    duracion_total = 0.0
    motor_usado = None

    for m in orden:
        if m == "pyttsx3":
            funcion = _con_pyttsx3
        elif m == "gtts":
            funcion = _con_gtts
        elif m == "espeak":
            funcion = _con_espeak
        elif m == "openai":
            funcion = _con_openai
        elif m == "elevenlabs":
            funcion = _con_elevenlabs
        else:
            continue

        # Probar el motor con el primer fragmento (si falla, pasa al siguiente)
        if m == "gtts":
            resultado = funcion(fragmentos[0], idioma)
        elif m in ["openai", "elevenlabs"]:
            resultado = funcion(fragmentos[0])
        else:
            resultado = funcion(fragmentos[0], velocidad)
            
        if resultado is None:
            continue

        motor_usado = m
        for idx, frag in enumerate(fragmentos):
            if m == "gtts":
                audio_parcial, fmt, dur = funcion(frag, idioma)
            elif m in ["openai", "elevenlabs"]:
                audio_parcial, fmt, dur = funcion(frag)
            else:
                audio_parcial, fmt, dur = funcion(frag, velocidad)
                
            audio_final += audio_parcial
            duracion_total += dur
            formato_final = fmt
        break

    if motor_usado is None:
        raise TTSError("Ningun motor TTS disponible. Revisa tus API keys o instala pyttsx3/gtts.")

    # Guardar a archivo si se solicito
    archivo_path = None
    if guardar_como:
        guardar_como = Path(guardar_como)
        guardar_como.write_bytes(audio_final)
        archivo_path = guardar_como
    return {
        "exito": True,
        "motor_usado": motor_usado,
        "audio_bytes": audio_final if devolver_bytes else None,
        "archivo": archivo_path,
        "formato": formato_final,
        "duracion_seg": duracion_total,
        "fragmentos": len(fragmentos),
    }

def reproducir(
    texto: str,
    cfg: Optional[Any] = None,
    motor: str = "auto",
    velocidad: int = 150,
    limite_fragmento: int = 500
) -> None:
    """
    Reproduce el texto directamente por el altavoz (sin guardar archivo).
    Es un atajo comodo para pruebas.
    """
    # Sintetizar a un archivo temporal
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        sintetizar(
            texto, cfg, motor, velocidad=velocidad, limite_fragmento=limite_fragmento,
            guardar_como=tmp_path, devolver_bytes=False
        )
        # Reproducir segun SO
        if sys.platform == "win32":
            import winsound
            winsound.PlaySound(str(tmp_path), winsound.SND_FILENAME)
        elif sys.platform == "darwin":
            import subprocess
            subprocess.run(["afplay", str(tmp_path)], check=False)
        else:
            import subprocess
            subprocess.run(["aplay", str(tmp_path)], check=False)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

# --- Adaptadores ---
def speak(text: str, output_file: str = None, motor: str = "auto", velocidad: int = 150):
    """
    Funcion simple para hablar o guardar audio.
    - Si output_file es None, reproduce directamente.
    - Si output_file es una ruta, guarda el audio ahi.
    """
    if output_file:
        return sintetizar(text, motor=motor, velocidad=velocidad, guardar_como=Path(output_file), devolver_bytes=False)
    else:
        return reproducir(text, motor=motor, velocidad=velocidad)