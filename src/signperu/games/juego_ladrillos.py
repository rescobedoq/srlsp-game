#src/signperu/games/juego_ladrillos.py
from .base_game import BaseGame

class JuegoLadrillos(BaseGame):
    def start(self):
        print("Juego Ladrillos iniciado for user", self.user)

    def stop(self):
        print("Juego Ladrillos detenido")

    def on_event(self, event):
        if event.get('type') == 'letter':
            print("[Ladrillos] letra:", event.get('letter'))
