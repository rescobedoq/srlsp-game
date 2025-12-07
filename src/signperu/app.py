#srlsp-game/src/signperu/app.py
# Script de arranque: crea contexto (EventBus, cola de frames, DB, juego)
# y arranca la GUI principal (MainWindow).
#
# NOTAS:
# - La UI (MainWindow) controla cuándo arrancar/ detener los hilos de captura
#   y procesamiento (mediante los botones Iniciar/Detener).
# - El juego se suscribe al EventBus para recibir eventos "detection".
# - La ventana principal debe ejecutarse en el hilo principal
from signperu.core.events import EventBus
from signperu.core.capture import CaptureThread
from signperu.core.processing import ProcessingThread
from signperu.core.detector import DetectorWrapper
from signperu.persistence.db_manager import DBManager
from signperu.games.juego_AH import JuegoAH
from queue import Queue
import os

# simple config: arranque que arma EventBus, hilos y la ventana del juego
class _C:
    CAMERA_SRC = 0
    FPS = 12
    DB_PATH = os.path.join("data", "signperu.db")

config = _C()

def run():
    event_bus = EventBus()
    db = DBManager.get_instance(config.DB_PATH)

    frame_q = Queue(maxsize=2)
    capture = CaptureThread(event_bus, src=config.CAMERA_SRC, target_fps=config.FPS, frame_queue=frame_q)
    detector = DetectorWrapper()
    processing = ProcessingThread(event_bus, detector, frame_q)

    # start threads
    capture.start()
    processing.start()

    # start GUI game AH
    game = JuegoAH(event_bus, db=db, config=None, user=None)
    try:
        game.start()   # Bloqueante: crea su propia ventana CTk
    finally:
        # Stop threads on exit
        capture.stop()
        processing.stop()
        db.close()

if __name__ == "__main__":
    run()
