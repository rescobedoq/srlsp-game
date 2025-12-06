#srlsp-game/src/signperu/core/events.py
# Bus de eventos sencillo para desacoplar detector -> UI / juegos / logger
import threading

class EventBus:
    def __init__(self):
        self._subs = {}
        self._lock = threading.Lock()

    def subscribe(self, event_name, callback):
        """Suscribe una función (callback) a un evento."""
        with self._lock:
            self._subs.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name, callback):
        """Quita una suscripción."""
        with self._lock:
            if event_name in self._subs and callback in self._subs[event_name]:
                self._subs[event_name].remove(callback)

    def publish(self, event_name, data=None):
        """Publica un evento; las callbacks se ejecutan en el hilo que publica."""
        callbacks = []
        with self._lock:
            callbacks = list(self._subs.get(event_name, []))
        for cb in callbacks:
            try:
                cb(data)
            except Exception as e:
                # No dejamos que una excepción rompa el bus
                print(f"[EventBus] Error en callback {cb}: {e}")
