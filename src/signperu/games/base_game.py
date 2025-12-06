#srlsp-game/src/signperu/games/base_game.py
# Clase abstracta que define la interfaz de un minijuego
from abc import ABC, abstractmethod

class Game(ABC):
    def __init__(self, app_context):
        """
        app_context: diccionario u objeto con dependencias (event_bus, db, usuario, etc.)
        """
        self.context = app_context
        self.running = False

    @abstractmethod
    def start(self):
        """Inicia el juego (preparar estado)."""
        self.running = True

    @abstractmethod
    def stop(self):
        """Detiene el juego y limpia estados."""
        self.running = False

    @abstractmethod
    def on_detection(self, token):
        """Se invoca cuando llega una detección de seña (token)."""
        pass

    def on_frame(self, frame):
        """Opcional: recibir frames para render o lógica"""
        pass

