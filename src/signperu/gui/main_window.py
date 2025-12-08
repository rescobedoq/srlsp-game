#srlsp-game/src/signperu/gui/main_window.py
# Interfaz principal usando CustomTkinter.
# Muestra visor de cámara (frames recibidos por EventBus) y recibe eventos "detection".
#
# Requisitos: customtkinter, pillow, opencv-python, numpy
#
# Diseño:
# - La UI NO manipula frames directamente desde hilos secundarios. Se suscribe al EventBus
#   con callbacks ligeros que colocan frames en una queue thread-safe.
# - El loop de Tk usa after() para consumir la queue y actualizar la imagen en el Label.
# - Botones: Iniciar captura, Detener captura, Seleccionar juego (placeholder), Salir.
# - Muestra un texto con la última detección por unos segundos.

