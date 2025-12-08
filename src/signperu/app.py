#srlsp-game/src/signperu/app.py
# Script de arranque: crea contexto (EventBus, cola de frames, DB, juego)
# y arranca la GUI principal (MainWindow).
#
# NOTAS:
# - La UI (MainWindow) controla cuándo arrancar/ detener los hilos de captura
#   y procesamiento (mediante los botones Iniciar/Detener).
# - El juego se suscribe al EventBus para recibir eventos "detection".
# - La ventana principal debe ejecutarse en el hilo principal
import argparse
import os
import sys
from queue import Queue
from signperu.core.events import EventBus
from signperu.core.capture import CaptureThread
from signperu.core.processing import ProcessingThread
from signperu.core.detector import DetectorWrapper
from signperu.persistence.db_manager import DBManager

"""
Launcher compacto para pruebas: arranca EventBus, hilos (capture/processing)
y lanza el juego seleccionado (AH / LC / LADRILLOS).

Uso:
  python -m signperu.app --game AH
  python -m signperu.app --game LC
  python -m signperu.app            # pide selección por consola
"""
# Intentamos importar los juegos disponibles
try:
    from signperu.games.juego_AH import JuegoAH
except Exception as e:
    JuegoAH = None
    # print("No se pudo importar JuegoAH:", e)

try:
    from signperu.games.juego_lc import JuegoLC
except Exception as e:
    JuegoLC = None
    # print("No se pudo importar JuegoLC:", e)

try:
    from signperu.games.juego_ladrillos import JuegoLadrillos
except Exception as e:
    JuegoLadrillos = None
    # print("No se pudo importar JuegoLadrillos:", e)

# Config simple
class _C:
    CAMERA_SRC = 0
    FPS = 12
    DB_PATH = os.path.join("data", "signperu.db")
config = _C()

# Mapeo nombre -> clase (si están importadas)
GAME_MAP = {
    "AH": JuegoAH,
    "LC": JuegoLC,
    "LADRILLOS": JuegoLadrillos,
}

def choose_game_interactive():
    options = [k for k,v in GAME_MAP.items() if v is not None]
    if not options:
        print("No hay ningún juego importable. Revisa tus archivos en signperu/games.")
        sys.exit(1)
    print("Juegos disponibles:")
    for i, name in enumerate(options, start=1):
        print(f"  {i}. {name}")
    sel = input(f"Elige juego (1-{len(options)}): ").strip()
    try:
        idx = int(sel) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except Exception:
        pass
    print("Selección no válida. Saliendo.")
    sys.exit(1)

def run(selected_game_key=None):
    # elegir juego si no se pasó por argumento
    if not selected_game_key:
        selected_game_key = choose_game_interactive()

    selected_game_key = selected_game_key.upper()
    game_cls = GAME_MAP.get(selected_game_key)
    if game_cls is None:
        print(f"Juego '{selected_game_key}' no disponible o no importado.")
        print("Disponibles:", [k for k,v in GAME_MAP.items() if v is not None])
        return

    # crear infra (EventBus, DB, hilos)
    event_bus = EventBus()
    db = DBManager.get_instance(config.DB_PATH)

    frame_q = Queue(maxsize=2)
    capture = CaptureThread(event_bus, src=config.CAMERA_SRC, target_fps=config.FPS, frame_queue=frame_q)
    detector = DetectorWrapper()
    processing = ProcessingThread(event_bus, detector, frame_q)

    # arrancar hilos antes de lanzar la UI/juego (para que haya feed y detecciones)
    capture.start()
    processing.start()
    print("[app] Hilos capture & processing iniciados.")

    # crear instancia del juego y ejecutarlo (bloqueante)
    try:
        game = game_cls(event_bus=event_bus, db=db, config=config, user=None)
        print(f"[app] Lanzando juego: {selected_game_key} -> {game_cls}")
        game.start()   # bloqueante: entra el loop del juego
    except Exception as ex:
        print("[app] Error al ejecutar el juego:", ex)
    finally:
        # parada y limpieza (se ejecuta cuando el juego termina o falla)
        print("[app] Deteniendo hilos y cerrando BD...")
        try:
            capture.stop()
        except Exception:
            pass
        try:
            processing.stop()
        except Exception:
            pass
        try:
            db.close()
        except Exception:
            pass
        print("[app] Salida limpia.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launcher de pruebas para juegos SignPeru.")
    parser.add_argument("--game", type=str, help="Clave del juego a ejecutar (AH, LC, LADRILLOS)")
    parser.add_argument("--menu", action="store_true", help="Forzar menu interactivo")
    args = parser.parse_args()

    selected = None
    if args.menu:
        selected = None
    elif args.game:
        selected = args.game
    else:
        # si no hay args, usamos prompt interactivo
        selected = None

    run(selected_game_key=selected)
