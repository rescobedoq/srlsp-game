#srlsp-game/src/signperu/core/events.py
# Bus de eventos sencillo para desacoplar detector -> UI / juegos / logger
import threading
from collections import defaultdict

class EventBus:
    """Pub/Sub simple y thread-safe."""
    def __init__(self):
        self._subs = defaultdict(list)
        self._lock = threading.RLock()

    def subscribe(self, event_name, callback):
        with self._lock:
            self._subs[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        with self._lock:
            if callback in self._subs[event_name]:
                self._subs[event_name].remove(callback)

    def publish(self, event_name, *args, **kwargs):
        with self._lock:
            subs = list(self._subs[event_name])
        for cb in subs:
            try:
                cb(*args, **kwargs)
            except Exception as e:
                # Solo logueamos, no fallamos todo el bus
                print(f"[EventBus] handler error for {event_name}: {e}")
