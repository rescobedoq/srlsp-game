#srlsp-game/src/signperu/games/juego_ah.py
# juego_AH.py
# Juego simple: cuando detecta la letra esperada cuenta éxito
from signperu.games.game_base import Game

class JuegoAH(Game):
    def __init__(self, app_context, target_letter='A'):
        super().__init__(app_context)
        self.target = target_letter
        self.attempts = 0
        self.successes = 0

    def start(self):
        super().start()
        self.attempts = 0
        self.successes = 0
        print(f"[JuegoAH] Iniciado. Objetivo: {self.target}")

    def stop(self):
        super().stop()
        print(f"[JuegoAH] Detenido. Intentos: {self.attempts}, Éxitos: {self.successes}")

    def on_detection(self, token):
        # lógica simple: si token == target -> éxito
        self.attempts += 1
        if token == self.target:
            self.successes += 1
            print(f"[JuegoAH] Éxito detectado: {token} (total éxitos: {self.successes})")
        else:
            print(f"[JuegoAH] Detección: {token} (no coincide con {self.target})")
        # persistir progreso (si se dispone de DB)
        db = self.context.get("db")
        user = self.context.get("user")
        if db and user:
            db.save_score(user["id"], "AH", self.successes, details=f"attempts={self.attempts}")
