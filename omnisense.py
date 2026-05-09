# omnisense.py
# Libreria principal: une ia.py, tts.py, graficas.py, eventos.py
#
# USO:
#   from omnisense import analizar_y_responder
#
#   # Analizar cualquier archivo y recibir respuesta en audio
#   analizar_y_responder("documento.pdf", "Resume esto", "respuesta.mp3")
#   analizar_y_responder("foto.jpg",      "Que hay aqui", "respuesta.mp3")
#   analizar_y_responder("datos.xlsx",    "Analiza los datos", "respuesta.mp3")
#
#   # Desde microfono
#   analizar_por_voz("codigo.py", "respuesta.mp3")
#
#   # Desde grafica matplotlib
#   import matplotlib.pyplot as plt
#   fig, ax = plt.subplots()
#   ax.plot([1,2,3],[3,1,2])
#   analizar_grafica(fig, "Describe esta grafica", "respuesta.mp3")

from ia  import analizar, verificar_conexion
from tts import guardar_audio, hablar, escuchar_seguro
from graficas import capturar_como_bytes


def analizar_y_responder(ruta_archivo, pregunta, ruta_audio_salida="respuesta.mp3"):
    """
    Funcion principal de la libreria.

    Recibe CUALQUIER tipo de archivo, lo analiza con la IA,
    y devuelve la respuesta como archivo de audio.

    Parametros:
        ruta_archivo      -- ruta al archivo a analizar
        pregunta          -- que quieres saber sobre el archivo
        ruta_audio_salida -- donde guardar la respuesta de audio

    Retorna:
        (respuesta_texto, ruta_audio)
    """
    print(f"\nAnalizando: {ruta_archivo}")
    print(f"Pregunta: {pregunta}")

    # 1. La IA analiza el archivo
    respuesta = analizar(ruta_archivo, pregunta)
    print(f"\nRespuesta:\n{respuesta}")

    # 2. Convertir respuesta a audio
    guardar_audio(respuesta, ruta_audio_salida)

    return respuesta, ruta_audio_salida


def analizar_por_voz(ruta_archivo, ruta_audio_salida="respuesta.mp3"):
    """
    Escucha la pregunta del usuario por microfono,
    analiza el archivo y responde con audio.

    Parametros:
        ruta_archivo      -- archivo a analizar
        ruta_audio_salida -- donde guardar la respuesta

    Retorna:
        (respuesta_texto, ruta_audio)
    """
    # 1. Escuchar pregunta por microfono
    pregunta = escuchar_seguro()
    if pregunta is None:
        print("No se entendio la pregunta.")
        return None, None

    # 2. Analizar y responder
    return analizar_y_responder(ruta_archivo, pregunta, ruta_audio_salida)


def analizar_grafica(figura_matplotlib, pregunta, ruta_audio_salida="respuesta.mp3"):
    """
    Analiza una grafica matplotlib con la IA y responde con audio.
    La grafica no necesita guardarse a disco.

    Parametros:
        figura_matplotlib -- objeto fig de matplotlib
        pregunta          -- que quieres saber sobre la grafica
        ruta_audio_salida -- donde guardar la respuesta

    Retorna:
        (respuesta_texto, ruta_audio)
    """
    print(f"\nAnalizando grafica...")
    print(f"Pregunta: {pregunta}")

    # 1. Capturar grafica como bytes PNG
    datos_png = capturar_como_bytes(figura_matplotlib)

    # 2. La IA analiza la imagen
    respuesta = analizar(datos_png, pregunta, tipo_mime="image/png")
    print(f"\nRespuesta:\n{respuesta}")

    # 3. Convertir respuesta a audio
    guardar_audio(respuesta, ruta_audio_salida)

    return respuesta, ruta_audio_salida


# ── DEMO ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== omnisense ===")
    print("Libreria para analizar archivos con IA y responder con audio\n")

    # Verificar conexion con OpenAI
    if not verificar_conexion():
        print("\nError: configura tu OPENAI_API_KEY primero.")
        print("  Windows: set OPENAI_API_KEY=tu_key")
        print("  Linux/Mac: export OPENAI_API_KEY=tu_key")
        exit(1)

    print("\nUso de ejemplo:")
    print("  from omnisense import analizar_y_responder")
    print('  analizar_y_responder("archivo.pdf", "Resume esto", "respuesta.mp3")')
    print('  analizar_y_responder("foto.jpg", "Que hay aqui?", "respuesta.mp3")')
    print('  analizar_y_responder("codigo.py", "Encuentra los bugs", "respuesta.mp3")')
