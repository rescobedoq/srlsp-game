#srlsp-game/src/signperu/core/processing.py
# Toma frames desde una queue, ejecuta el detector y publica eventos al EventBus
# ProcessingThread refactorizado que soporta inyección de Strategy (patrón Strategy)
# y utiliza logging. Publica eventos adicionales en EventBus para facilitar tracing.

#import time
#Import de la interfaz Strategy (si se quiere proporcionar directamente)
#from signperu.core.strategies import ProcessingStrategy, SimpleProcessingStrategy
import threading
from queue import Queue, Empty

class ProcessingThread(threading.Thread):
    """
    Hilo consumidor: toma frames desde frame_queue, ejecuta detector.detect_from_frame()
    y publica eventos 'hand_detected' con (letra, frame_annotated).
    """
    def __init__(self, event_bus, detector, frame_queue:Queue):
        super().__init__(daemon=True)
        self.event_bus = event_bus
        self.detector = detector
        self.frame_queue = frame_queue
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.5)
            except Empty:
                continue
            # src/signperu/core/processing.py (dentro del while)
            try:
                letra, frame_proc, coords = self.detector.detect_from_frame(frame)
                if coords:
                    """ #Solo para comprobar que detecta las manos
                    try:
                        print("[ProcessingThread] detected:", letra, "landmarks(0:5):", coords[:5])
                    except Exception:
                        print("[ProcessingThread] detected:", letra, "landmarks count:", len(coords))
                    """
                # Publicamos coords como 'landmarks' para quien quiera verlas
                self.event_bus.publish("hand_detected", letra, frame=frame_proc, landmarks=coords)
            except Exception as e:
                print("[ProcessingThread] error:", e)

    def stop(self):
        self.running = False