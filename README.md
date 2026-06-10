# Mobility Assist: Prototipo de Asistencia Visual y Navegación

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Ultralytics YOLO](https://img.shields.io/badge/YOLOv8-Ultralytics-orange?logo=ultralytics)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4-A22846?logo=raspberrypi&logoColor=white)
![Nvidia](https://img.shields.io/badge/NVIDIA-CUDA-76B900?logo=nvidia&logoColor=white)
![NCNN](https://img.shields.io/badge/Inferencia-NCNN%20Optimized-brightgreen)

Este proyecto implementa un sistema híbrido de asistencia visual y navegación. El procesamiento pesado (entrenamiento del modelo) se realiza en una estación de trabajo o PC con **GPU dedicada**, mientras que la inferencia en tiempo real (**Edge Computing**) se ejecuta de forma optimizada mediante el framework **NCNN** en una **Raspberry Pi 4**.

---

## 📋 Arquitectura General del Sistema

1. **Fase de Entrenamiento (PC):** Generación de pesos optimizados con CUDA y exportación al formato ligero NCNN.
2. **Fase de Despliegue (Edge):** Inferencia asíncrona en hardware de borde integrado con APIs de geolocalización e interfaces de voz.

---

## 🧠 1. Entrenamiento del Modelo (PC)

Para entrenar el modelo de detección de objetos, se utilizó una GPU NVIDIA y el framework Ultralytics. Las clases objetivo son:
* `Stairs` (Escaleras)
* `faded_crosswalk` (Pasos peatonales desgastados)
* `intact_crosswalk` (Pasos peatonales intactos)

### 🔧 Requisitos y Configuración

1. Clone su dataset balanceado desde **Roboflow** en la carpeta raíz del proyecto.
2. Cree un entorno virtual de Python e instale las dependencias necesarias:

```bash
# Crear entorno virtual
python -m venv yolov8_env

# Activar entorno virtual
# En Linux/Mac:
source yolov8_env/bin/activate  
# En Windows:
# yolov8_env\Scripts\activate   

# Instalar Framework Ultralytics YOLO
pip install ultralytics
```

### 🚀 Uso

Ejecute el script de entrenamiento para procesar las clases descritas. El script detectará y utilizará automáticamente la aceleración por hardware **CUDA** si los drivers de NVIDIA están correctamente configurados en el sistema host.

```bash
python train.py
```

Los pesos resultantes se guardarán automáticamente en la ruta:
`runs/detect/train/weights/best.pt`

> 💡 **Nota:** Al finalizar el entrenamiento, el modelo se exportará a formato **NCNN** a la ruta indicada en consola para poder migrarlo a la Raspberry Pi.

---

## 💻 2. Pruebas Locales (PC)

Antes de desplegar el modelo en el hardware de borde final, se recomienda validar su tasa de acierto y rendimiento general utilizando la cámara web de la computadora.

### 🚀 Uso

Asegúrese de que el archivo de pesos `best.pt` esté referenciado de manera correcta en el script de pruebas de escritorio. Luego ejecute:

```bash
python pc_test.py
```

* Se abrirá una ventana de renderizado mediante **OpenCV** mostrando el flujo de la cámara web.
* Apunte la cámara hacia imágenes de escaleras o pasos peatonales para verificar que los *Bounding Boxes* se adhieren con una confianza **superior al 78%**.
* Presione la tecla **`q`** enfocando la ventana de video para finalizar la ejecución.

---

## 🍓 3. Despliegue en Raspberry Pi (Hardware Final)

El script maestro combina la visión artificial asíncrona con el escaneo del entorno Wi-Fi y la interacción con la API de Google Maps para proporcionar una asistencia integral.

### ⚙️ Configuración del Entorno (Debian 13)

Desde la terminal nativa de la Raspberry Pi, instale las herramientas esenciales del sistema operativo:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-venv python3-pyaudio flac espeak network-manager python3-picamera2 -y
```

> ⚠️ **Recomendación de Almacenamiento:** Dado que el almacenamiento local de la tarjeta MicroSD puede ser una limitante de rendimiento y espacio, se sugiere encarecidamente crear el entorno virtual en un almacenamiento externo (Pendrive USB / SSD) o expandir el sistema de archivos mediante el comando `sudo raspi-config`.

### 📦 Instalación de Dependencias Python

Genere un entorno aislado compartiendo los paquetes del sistema e instale las bibliotecas de IA y Geolocalización:

```bash
# Crear entorno virtual con acceso a paquetes del sitio del sistema
python3 -m venv assist_env --system-site-packages
source assist_env/bin/activate

# Instalar dependencias sin almacenamiento en caché para optimizar espacio
pip install ultralytics opencv-python-headless ncnn SpeechRecognition googlemaps --no-cache-dir
```

### 🔑 Configuración de la API

1. Copie el script principal `master_assist.py` junto con el directorio del modelo **NCNN** entrenado a la carpeta de trabajo en la Raspberry Pi.
2. Abra el archivo `master_assist.py` con su editor de preferencia.
3. Ubique la variable global `GMAPS_API_KEY` y reemplace su valor con su clave de acceso credencializada de **Google Cloud Console**.

```python
# master_assist.py
GMAPS_API_KEY = "TU_API_KEY_AQUÍ"
```
*(Nota: Por motivos estrictos de seguridad, las claves de desarrollo no se encuentran incluidas en este repositorio).*

### 🛠️ Uso del Prototipo

Cerciórese de que la cámara CSI (o Raspberry Pi Camera Module) y el micrófono por interfaz USB estén debidamente conectados y reconocidos por el kernel. Active el entorno e inicialice el núcleo del servicio:

```bash
source assist_env/bin/activate
python3 master_assist.py
```
