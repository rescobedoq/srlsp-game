#srlsp-game/src/signperu/games/game_base.py
# Clase abstracta que define la interfaz de un minijuego
from abc import ABC, abstractmethod
import abc

class GameBase(abc.ABC):
    """
    Interfaz base que los juegos deben seguir.
    El juego puede ser una ventana propia o un frame embebido.
    """
    def __init__(self, event_bus, db=None, config=None, user=None):
        self.event_bus = event_bus
        self.db = db
        self.config = config or {}
        self.user = user

    @abc.abstractmethod
    def start(self):
        """Inicia el juego (mostrar UI, subscribir eventos)."""
        raise NotImplementedError()

    @abc.abstractmethod
    def stop(self):
        """Detener y limpiar recursos (desubscribir eventos, cerrar cámara si aplica)."""
        raise NotImplementedError()

    @abc.abstractmethod
    def on_hand_detected(self, letra, frame=None):
        """Callback que recibe detecciones de mano."""
        raise NotImplementedError()

    def save_score(self, score, game_name=None):
        if self.db:
            game = game_name or self.__class__.__name__
            try:
                self.db.execute(
                    "INSERT INTO scores (user_id, game, score, duration) VALUES (?, ?, ?, ?)",
                    (None, game, score, 0.0)
                )
            except Exception as e:
                print("[GameBase] guardar score:", e)
