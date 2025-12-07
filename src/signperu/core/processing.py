#srlsp-game/src/signperu/core/processing.py
# Toma frames desde una queue, ejecuta el detector y publica eventos al EventBus
# ProcessingThread refactorizado que soporta inyección de Strategy (patrón Strategy)
# y utiliza logging. Publica eventos adicionales en EventBus para facilitar tracing.

#import time
#from queue import Queue, Empty
#from signperu.core.events import EventBus
#from signperu.core.detector import DetectorSenias
#from signperu.utils.logger import get_logger
#from signperu import config
# Import de la interfaz Strategy (si se quiere proporcionar directamente)
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
            try:
                letra, frame_proc = self.detector.detect_from_frame(frame)
                # Publicar incluso si letra==None para que GUI muestre el feed
                self.event_bus.publish("hand_detected", letra, frame=frame_proc)
            except Exception as e:
                print("[ProcessingThread] error:", e)

    def stop(self):
        self.running = False


      