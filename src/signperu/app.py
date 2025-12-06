#srlsp-game/src/signperu/app.py
# Script de arranque: crea contexto (EventBus, cola de frames, DB, juego)
# y arranca la GUI principal (MainWindow).
#
# NOTAS:
# - La UI (MainWindow) controla cuándo arrancar/ detener los hilos de captura
#   y procesamiento (mediante los botones Iniciar/Detener).
# - El juego se suscribe al EventBus para recibir eventos "detection".
# - La ventana principal debe ejecutarse en el hilo principal (por eso usamos mainloop()).
# - Conserva el uso de DBManager (Singleton) y crea un usuario de prueba "test_user".
import time
from queue import Queue

from signperu.core.events import EventBus
from signperu.persistence.db_manager import DBManager
from signperu.games.juego_AH import JuegoAH
from signperu.gui.main_window import MainWindow
from signperu.core.capture import CaptureThread
from signperu.core.processing import ProcessingThread
from signperu import config

def main():
    # Cola de frames compartida (será utilizada por CaptureThread y ProcessingThread)
    frame_queue = Queue(maxsize=4)

    # Bus de eventos para desacoplar componentes
    event_bus = EventBus()

    # Inicializamos DB (Singleton) y creamos un usuario de prueba
    db = DBManager()  # usa config.DB_PATH por defecto
    user_id = db.create_user("test_user")
    user = db.get_user("test_user")

    # Contexto compartido para los juegos
    app_context = {"event_bus": event_bus, "db": db, "user": user}

    # Creamos la instancia del juego (no se inicia en cuanto a threads; solo la lógica)
    juego = JuegoAH(app_context, target_letter='A')
    juego.start()  # inicializa estado interno del juego

    # Suscribimos el juego a eventos de detección para que reciba tokens
    event_bus.subscribe("detection", lambda token: juego.on_detection(token))

    # --- Creamos instancias de threads pero no las arrancamos aquí ---
    # La MainWindow iniciará los hilos cuando el usuario pulse "Iniciar captura".
    cap_thread = CaptureThread(frame_queue,
                               camera_index=config.CAMERA_INDEX,
                               width=config.FRAME_WIDTH,
                               height=config.FRAME_HEIGHT,
                               target_fps=config.TARGET_FPS)

    proc_thread = ProcessingThread(frame_queue, event_bus)

    # Creamos y arrancamos la GUI principal, pasando las dependencias necesarias.
    # MainWindow se encarga de iniciar/detener los hilos y cerrar la DB al salir.
    mw = MainWindow(event_bus=event_bus,
                    frame_queue=frame_queue,
                    capture_thread=cap_thread,
                    processing_thread=proc_thread,
                    db=db,
                    user=user)

    # Ejecutar la UI (bloqueante, debe ejecutarse en el hilo principal)
    mw.mainloop()

    # Cuando se cierra la ventana, MainWindow publica "quit" y ya intentó cerrar hilos y DB.
    # No obstante, por seguridad, hacemos una limpieza mínima adicional.
    try:
        if cap_thread:
            cap_thread.stop()
    except Exception:
        pass

    try:
        if proc_thread:
            proc_thread.stop()
    except Exception:
        pass

    try:
        db.close()
    except Exception:
        pass

    print("[app] Aplicación finalizada.")

if __name__ == "__main__":
    main()
