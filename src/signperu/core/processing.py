#srlsp-game/src/signperu/core/processing.py
# Toma frames desde una queue, ejecuta el detector y publica eventos al EventBus

import threading
import time
from queue import Queue, Empty
from signperu.core.events import EventBus
from signperu.core.detector import DetectorSenias
from signperu import config

class ProcessingThread(threading.Thread):
    def __init__(self, frame_queue: Queue, event_bus: EventBus, detector: DetectorSenias = None):
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.event_bus = event_bus
        self.detector = detector or DetectorSenias()
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=0.5)
            except Empty:
                continue
            try:
                token, annotated = self.detector.predict(frame)
                # publicamos siempre el frame anotado (para visor UI) y la detección si existe
                self.event_bus.publish("frame", annotated)
                if token:
                    # publicamos evento de detección con token
                    self.event_bus.publish("detection", token)
            except Exception as e:
                print(f"[ProcessingThread] Error procesando frame: {e}")
            # se puede añadir un pequeño sleep para regular CPU si es necesario
            time.sleep(0.001)

    def stop(self):
        self._stop_event.set()
