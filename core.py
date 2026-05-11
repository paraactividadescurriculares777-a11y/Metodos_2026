# core.py
# Autor: Carlos
# Adaptado para el NUEVO SDK de Gemini (google-genai) y unificado con el equipo

import os
import time
import base64
import pygame # Importamos pygame solo para el audio
from google import genai
from google.genai import types


from detector import detectar
from extractor import extraer
from tts import speak

# 1. Configuracion de la llave
llave_api = os.getenv("GEMINI_API_KEY")

if not llave_api:
    print("=========================================")
    print("ERROR: Falta la GEMINI_API_KEY.")
    print("Por favor, agregala a tus variables de entorno.")
    print("=========================================")
    exit()

# 2. Inicializar el cliente NUEVO de Gemini
client = genai.Client(api_key=llave_api)

# Usamos el modelo mas reciente y rapido
MODELO = "gemini-2.5-flash" 

def iniciar_omnisense(ruta_archivo, pregunta_usuario, datos_base64=None):
    try:
        if datos_base64:
            # ==================================================
            # MODO INTEGRACION: BASE64 DIRECTO EN MEMORIA
            # ==================================================
            print("\n--- [MODO ANALISIS DE CAPTURA OPENGL EN MEMORIA] ---")
            print("[1] Decodificando frame...")
            
            image_bytes = base64.b64decode(datos_base64)
            imagen_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/png',
            )
            
            print("[2] Consultando a Gemini...")
            response = client.models.generate_content(
                model=MODELO,
                contents=[imagen_part, pregunta_usuario]
            )
            texto_respuesta = response.text

        elif ruta_archivo:
            # ==================================================
            # MODO INTEGRACION: DETECCION Y EXTRACCION
            # ==================================================
            print("\n--- [MODO ANALISIS DE ARCHIVO] ---")
            
            categoria, mime_type, extra_info = detectar(ruta_archivo)
            print(f"[1] Archivo detectado por Dana: {categoria} ({mime_type})")

            print("[2] Extrayendo contenido...")
            # Aca usamos el modulo de Dana para sacar los datos
            datos_extraidos = extraer(ruta_archivo, categoria, extra_info, cfg=None)

            if datos_extraidos["tipo"] == "text":
                # Si se logro sacar el texto (de un PDF, DOCX, o codigo fuente)
                # se lo mandamos directo a Gemini en el prompt (es mas rapido)
                print("  > Texto extraido con exito. Evitando subida a la nube.")
                contenido_final = f"Archivo: {ruta_archivo}\nContenido:\n{datos_extraidos['contenido']}\n\nPregunta: {pregunta_usuario}"
                
                print("[3] Consultando a Gemini...")
                response = client.models.generate_content(
                    model=MODELO,
                    contents=contenido_final
                )
                texto_respuesta = response.text

            else:
                # Si es video, audio o imagen pesada, usamos el Files API original
                print("  > Archivo binario detectado. Usando Google Files API.")
                print("[3] Subiendo archivo a Gemini...")
                archivo_subido = client.files.upload(file=ruta_archivo)
                print(f"  > Archivo subido: {archivo_subido.name}")

                print("[4] Esperando procesamiento...")
                while archivo_subido.state.name == "PROCESSING":
                    time.sleep(1)
                    archivo_subido = client.files.get(name=archivo_subido.name)
                
                if archivo_subido.state.name == "FAILED":
                    raise Exception("El archivo fallo al procesarse en los servidores de Google.")

                print("[5] Consultando a Gemini...")
                response = client.models.generate_content(
                    model=MODELO,
                    contents=[archivo_subido, pregunta_usuario]
                )
                texto_respuesta = response.text

                #Limpiar
                client.files.delete(name=archivo_subido.name)
                print("[6] Archivo temporal eliminado de la nube")

        else:
            # ==================================================
            # MODO CHAT NORMAL
            # ==================================================
            print(f"\n[⚡] Consultando a Gemini ({MODELO})...")
            response = client.models.generate_content(
                model=MODELO,
                contents=pregunta_usuario
            )
            texto_respuesta = response.text

        # ==========================================
        # RESPUESTA Y AUDIO (Modificado con pygame)
        # ==========================================
        print("\n--- RESPUESTA DE LA IA ---")
        print(texto_respuesta)
        print("--------------------------\n")

        print("[*] Generando respuesta de voz...")
        # Genera el wav(mp3) usando tu modulo TTS
        speak(texto_respuesta, output_file="respuesta_final.wav")
        
        # Reproducimos el wav(mp3) con pygame para evitar el error de winsound
        pygame.mixer.init()
        pygame.mixer.music.load("respuesta_final.wav")
        pygame.mixer.music.play()
        
        # Mantiene el programa en pausa mientras la IA sigue hablando
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        # Opcional: apagar el mixer para liberar el archivo wav(mp3)
        pygame.mixer.quit()
        
        return texto_respuesta

    except Exception as error:
        print(f"\n[ERROR] Algo salio mal en el proceso: {error}")
        return None

# --- DEMO ---
if __name__ == "__main__":
    print("=== BIENVENIDO A OMNISENSE (Gemini 2.5) ===")
    print("Escribe 'salir' para cerrar el programa.")
    print("Escribe una pregunta para chatear, o pega la RUTA de un archivo para analizarlo.\n")
    
    while True:
        entrada = input("Tu: ").strip()
        if entrada.lower() == 'salir':
            break
        if not entrada:
            continue
            
        entrada_limpia = entrada.strip("'").strip('"')
        
        if os.path.exists(entrada_limpia) and os.path.isfile(entrada_limpia):
            pregunta_archivo = input("IA: Veo que es un archivo. ¿Que quieres que haga con el?: ")
            iniciar_omnisense(ruta_archivo=entrada_limpia, pregunta_usuario=pregunta_archivo)
        else:
            iniciar_omnisense(ruta_archivo="", pregunta_usuario=entrada)