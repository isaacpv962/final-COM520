import cv2
import time
import os
import threading
import re
import subprocess
import speech_recognition as sr
import googlemaps
from ultralytics import YOLO
from picamera2 import Picamera2

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================

# IMPORTANTE: Reemplaza esto por tu clave real
GMAPS_API_KEY = ""

# VARIABLES DE COMPORTAMIENTO
USE_MICROPHONE = False         # Cambia a True cuando conectes un micrófono USB
CONFIDENCE_THRESHOLD = 0.78    # Umbral de IA (78%)
PROXIMITY_THRESHOLD = 0.20     # El objeto debe ocupar el 20% de la cámara
COOLDOWN_SECONDS = 10.0        # Espera 10 segundos antes de repetir

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best_ncnn_model")

gmaps = googlemaps.Client(key=GMAPS_API_KEY)
recognizer = sr.Recognizer()

VOICE_CMD_BASE = ["espeak", "-v", "es", "-s", "140"]

def speak(text, wait=False):
    """Reproduce voz usando espeak."""
    try:
        text = str(text).replace('"', "")
        cmd = VOICE_CMD_BASE + [text]

        if wait:
            subprocess.run(cmd)
        else:
            subprocess.Popen(cmd)
    except Exception as e:
        print(f"[Error voz]: {e}")

def clean_instruction(raw_html):
    """Limpia etiquetas HTML y adapta direcciones cardinales para personas no videntes."""
    # 1. Reemplazar etiquetas HTML con un ESPACIO
    cleanr = re.compile("<.*?>")
    text = re.sub(cleanr, " ", raw_html)
    
    # 2. Limpiar dobles espacios accidentales
    text = re.sub(r"\s+", " ", text).strip()
    
    # 3. Eliminar sin piedad cualquier mención cardinal (al norte, hacia el sur, etc.)
    cardinales = re.compile(r"(?i)\b(al|hacia\s*el|hacia|en\s*direcci[óo]n)\s+(norte|sur|este|oeste|noreste|noroeste|sureste|suroeste)\b")
    text = re.sub(cardinales, "", text)
    
    # 4. Cambiar cualquier verbo de movimiento errático de Google por un simple "Avanza"
    verbos = re.compile(r"(?i)\b(dir[íi]gete|camina|ve|sigue)\b")
    text = re.sub(verbos, "Avanza", text)
    
    # 5. Limpiar espacios dobles que pudieron quedar tras borrar las palabras cardinales
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

# ==========================================
# GEOLOCALIZACIÓN Y RUTAS
# ==========================================

def get_wifi_macs():
    """Escanea routers Wi-Fi cercanos usando Expresiones Regulares."""
    try:
        result = subprocess.run(
            ["sudo", "nmcli", "-t", "-f", "BSSID", "dev", "wifi", "list"],
            capture_output=True, text=True
        )
        
        # Usamos Regex para atrapar las MAC ignorando caracteres invisibles (\r, \n, \:)
        mac_pattern = re.compile(r"([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})")
        valid_macs = []
        
        for line in result.stdout.split("\n"):
            # A veces nmcli escapa los dos puntos (ej. 36\:40...), los limpiamos primero
            clean_line = line.replace('\\:', ':')
            match = mac_pattern.search(clean_line)
            if match:
                valid_macs.append(match.group(0))
        
        # Elimina duplicados usando set()
        valid_macs = list(set(valid_macs))
        
        if not valid_macs:
            print(f"[Debug Wi-Fi] No pude extraer MACs. Salida cruda de nmcli: {result.stdout.strip()}")
            
        return valid_macs
    except Exception as e:
        print(f"[Error al ejecutar nmcli]: {e}")
        return []

def get_live_coordinates():
    macs = get_wifi_macs()
    wifi_data = [{"macAddress": mac} for mac in macs[:5]]

    try:
        if wifi_data:
            print(f"[Ubicación] {len(macs)} routers detectados. Triangulando posición con Google...")
            loc = gmaps.geolocate(wifi_access_points=wifi_data)
        else:
            print("[Ubicación] Sin Wi-Fi. Usando ubicación por IP (Baja precisión)...")
            loc = gmaps.geolocate()

        lat = loc["location"]["lat"]
        lng = loc["location"]["lng"]
        print(f"[Ubicación] Coordenadas: {lat},{lng}")
        return f"{lat},{lng}"

    except Exception as e:
        print(f"[Error Google API]: {e}")
        return "-19.0431,-65.2592"

def calculate_and_speak_route(destination):
    speak(f"Buscando ruta hacia {destination}", wait=False)
    live_origin = get_live_coordinates()

    try:
        directions = gmaps.directions(
            live_origin, destination, mode="walking", language="es"
        )

        if not directions:
            print("[Navegación] No se encontró ruta.")
            speak("Lo siento, no pude encontrar una ruta.", wait=False)
            return

        steps = directions[0]["legs"][0]["steps"]
        print(f"[Navegación] Ruta a {destination} encontrada.")
        speak("Ruta encontrada. Leeré los primeros pasos.", wait=True)
        time.sleep(1)

        for i, step in enumerate(steps[:3]):
            instruction = clean_instruction(step["html_instructions"])
            print(f"[Paso {i + 1}]: {instruction}")
            speak(instruction, wait=True)
            time.sleep(1)
            
    except Exception as e:
        print(f"[Error de Ruta]: {e}")
        speak("Hubo un error de conexión con el mapa.", wait=False)

# ==========================================
# HILOS SECUNDARIOS: MÉTODOS DE NAVEGACIÓN
# ==========================================

def console_navigation_worker():
    time.sleep(2)
    print("\n" + "="*50)
    print(" MODO CONSOLA ACTIVADO (Sin Micrófono)")
    print(" Escribe un destino en cualquier momento y presiona Enter.")
    print("="*50 + "\n")
    
    while True:
        try:
            destination = input()
            if destination.strip():
                print(f"\n[Consola] Solicitando ruta a: {destination}")
                calculate_and_speak_route(destination)
        except Exception:
            pass

def voice_navigation_worker():
    print("[Voz] Módulo de micrófono iniciado.")
    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            destination = recognizer.recognize_google(audio, language="es-BO")
            print(f"\n[Voz] Has dicho: {destination}")
            calculate_and_speak_route(destination)

        except sr.UnknownValueError:
            pass 
        except sr.WaitTimeoutError:
            pass 
        except Exception as e:
            print(f"[Error de Micrófono]: {e}")
            time.sleep(2)

# ==========================================
# HILO PRINCIPAL: IA VISUAL YOLO
# ==========================================

def main():
    print("==========================================")
    print(" Prototipo Asistente de Movilidad Mejorado")
    print("==========================================")

    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] No se encontró el modelo en: {MODEL_PATH}")
        return

    if USE_MICROPHONE:
        nav_thread = threading.Thread(target=voice_navigation_worker, daemon=True)
    else:
        nav_thread = threading.Thread(target=console_navigation_worker, daemon=True)
    nav_thread.start()

    print("[IA] Cargando modelo YOLO/NCNN...")
    model = YOLO(MODEL_PATH)
    
    print("[Cámara] Iniciando...")
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 480)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()

    last_alert_time = 0
    print("[IA] Cámara activa. Evaluando entorno...")

    try:
        while True:
            frame = picam2.capture_array()
            frame_area = frame.shape[0] * frame.shape[1]

            results = model(frame, stream=True, verbose=False)

            for r in results:
                for box in r.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    proximity_ratio = (float(box.xywh[0][2]) * float(box.xywh[0][3])) / frame_area

                    if confidence > CONFIDENCE_THRESHOLD and proximity_ratio > PROXIMITY_THRESHOLD:
                        current_time = time.time()

                        if current_time - last_alert_time > COOLDOWN_SECONDS:
                            
                            if class_id == 0:
                                print(f"[IA] Escaleras detectadas! (Confianza: {confidence:.2f})")
                                speak("Atención, escaleras al frente", wait=False) 
                                last_alert_time = current_time

                            elif class_id in [1, 2]:
                                print(f"[IA] Paso Peatonal detectado! (Confianza: {confidence:.2f})")
                                speak("Cuidado, paso de cebra aproximándose", wait=False)
                                last_alert_time = current_time

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\n[Sistema] Apagando...")
    finally:
        try:
            picam2.stop()
        except:
            pass
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
