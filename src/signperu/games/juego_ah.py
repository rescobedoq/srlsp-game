#srlsp-game/src/signperu/games/juego_ah.py
from .base_game import BaseGame
import threading, time

class JuegoAH(BaseGame):
    def __init__(self, user, event_queue, db):
        super().__init__(user, event_queue, db)
        self._running = False

    def start(self):
        self._running = True
        print("Juego AH iniciado for user", self.user)
        # Example: consume queue in a separate thread
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self._running:
            try:
                ev = self.event_queue.get(timeout=0.5)
                self.on_event(ev)
            except Exception:
                pass
            time.sleep(0.01)

    def stop(self):
        self._running = False

    def on_event(self, event):
        if event.get('type') == 'letter':
            print("[AH] detected:", event.get('letter'), event.get('score'))
