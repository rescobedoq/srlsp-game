#src/signperu/games/base_game.py
from abc import ABC, abstractmethod

class BaseGame(ABC):
    def __init__(self, user, event_queue, db):
        self.user = user
        self.event_queue = event_queue
        self.db = db

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def on_event(self, event):
        """Handle events coming from recognizer (letter events)."""
        pass
