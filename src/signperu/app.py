#srlsp-game/src/signperu/app.py
# Script de arranque mínimo para probar captura + detector + eventos
import cv2
import time
from queue import Queue
from signperu.gui.main_window import MainWindow

from signperu.core.events import EventBus
from signperu.core.capture import CaptureThread
from signperu.core.processing import ProcessingThread
from signperu.persistence.db_manager import DBManager
from signperu.games.juego_AH import JuegoAH
from signperu import config

def main():
    # cola de frames (tamaño moderado para evitar latencia)
    frame_queue = Queue(maxsize=4)
    event_bus = EventBus()

    # inicializamos DB (singleton)
    db = DBManager()  # usa config.DB_PATH por defecto
    # crear usuario de prueba
    user_id = db.create_user("test_user")
    user = db.get_user("test_user")

    # contexto compartido para juegos
    app_context = {"event_bus": event_bus, "db": db, "user": user}

    # instanciamos juego de ejemplo y lo suscribimos a detecciones
    juego = JuegoAH(app_context, target_letter='A')
    juego.start()
    event_bus.subscribe("detection", lambda token: juego.on_detection(token))

    # suscripción para mostrar frames en una ventana cv2
    def show_frame(frame):
        cv2.imshow("Visor - Press q to quit", frame)
        # waitKey corto para mantener ventana responsiva
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # publicar evento de salida si se presiona q
            event_bus.publish("quit", None)

    event_bus.subscribe("frame", show_frame)

    # threads: captura y procesamiento
    cap_thread = CaptureThread(frame_queue, camera_index=config.CAMERA_INDEX,
                               width=config.FRAME_WIDTH, height=config.FRAME_HEIGHT,
                               target_fps=config.TARGET_FPS)
    proc_thread = ProcessingThread(frame_queue, event_bus)

    cap_thread.start()
    proc_thread.start()

    # suscribir quit para detener todo
    def on_quit(_):
        print("[app] Señal de salida recibida.")
        cap_thread.stop()
        proc_thread.stop()
        juego.stop()

    event_bus.subscribe("quit", on_quit)

    # loop principal simple: esperar hasta que los threads terminen o se solicite quit
    try:
        while cap_thread.is_alive() and proc_thread.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("[app] KeyboardInterrupt - cerrando...")
        cap_thread.stop()
        proc_thread.stop()
        juego.stop()

    # limpieza final
    cv2.destroyAllWindows()
    db.close()
    print("[app] Aplicación finalizada.")

if __name__ == "__main__":
    main()
