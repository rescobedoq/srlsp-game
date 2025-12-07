#srlsp-game/src/signperu/games/juego_lc.py
from .base_game import BaseGame

class JuegoLC(BaseGame):
    def start(self):
        print("Juego LC iniciado for user", self.user)

    def stop(self):
        print("Juego LC detenido")

    def on_event(self, event):
        if event.get('type') == 'letter':
            print("[LC] letra:", event.get('letter'))
