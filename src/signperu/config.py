#srlsp-game/src/signperu/config.py
# config.py
# Configuración global del proyecto (valores por defecto)
CAMERA_INDEX = 0            # índice de la cámara por defecto
FRAME_WIDTH = 640           # ancho de la imagen capturada
FRAME_HEIGHT = 480          # alto de la imagen capturada
TARGET_FPS = 20             # fps objetivo para captura/procesamiento
DETECTOR_SMOOTHING_WINDOW = 5  # tamaño de ventana para suavizado temporal
DETECTOR_CONFIRM_THRESHOLD = 3 # número mínimo de repeticiones para confirmar una detección
DB_PATH = "signperu/data/signperu.db"   # ruta de la base de datos SQLite (carpeta data/)
