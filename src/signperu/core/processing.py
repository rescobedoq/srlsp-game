#srlsp-game/src/signperu/core/processing.py
# Toma frames desde una queue, ejecuta el detector y publica eventos al EventBus

# processing.py
# ProcessingThread refactorizado que soporta inyección de Strategy (patrón Strategy)
# y utiliza logging. Publica eventos adicionales en EventBus para facilitar tracing.

import threading
import time
from queue import Queue, Empty

from signperu.core.events import EventBus
from signperu.core.detector import DetectorSenias
from signperu.utils.logger import get_logger
from signperu import config

# Import de la interfaz Strategy (si se quiere proporcionar directamente)
from signperu.core.strategies import ProcessingStrategy, SimpleProcessingStrategy

class ProcessingThread(threading.Thread):
    """
    Hilo que toma frames desde frame_queue, delega su procesamiento a una strategy
    y publica resultados en el EventBus.
    Parámetros:
        - frame_queue: Queue donde se obtienen frames (BGR OpenCV).
        - event_bus: EventBus para publicar eventos ("frame", "detection", etc.)
        - detector: instancia de DetectorSenias (si None, se crea una por defecto).
        - strategy: instancia de ProcessingStrategy (si None, se usa SimpleProcessingStrategy).
        - logger: logger opcional (si None, se obtiene con utils.logger.get_logger).
    """
    def __init__(self, frame_queue: Queue, event_bus: EventBus,
                 detector: DetectorSenias = None, strategy: ProcessingStrategy = None,
                 logger=None):
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.event_bus = event_bus or EventBus()
        self.detector = detector or DetectorSenias()
        # si se pasó una clase strategy ya instanciada la usamos, si se pasó None, creamos SimpleProcessingStrategy
        if strategy is None:
            self.strategy = SimpleProcessingStrategy(self.detector, event_bus=self.event_bus,
                                                     logger=get_logger("signperu.strategy"))
        else:
            # si se pasó un objeto strategy, verificar que es compatible
            if isinstance(strategy, ProcessingStrategy):
                self.strategy = strategy
            else:
                # si se pasó la clase, instanciarla (intento)
                try:
                    self.strategy = strategy(self.detector, event_bus=self.event_bus, logger=get_logger("signperu.strategy"))
                except Exception:
                    # fallback: usar SimpleProcessingStrategy
                    self.strategy = SimpleProcessingStrategy(self.detector, event_bus=self.event_bus,
                                                             logger=get_logger("signperu.strategy"))

        self.logger = logger or get_logger("signperu.processing")
        self._stop_event = threading.Event()

        # publicar configuración de la estrategia
        try:
            self.logger.debug(f"ProcessingThread creado con strategy={self.strategy.__class__.__name__}")
        except Exception:
            pass

    def run(self):
        self.logger.info("ProcessingThread iniciado.")
        while not self._stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=0.5)
            except Empty:
                continue

            try:
                token, annotated = self.strategy.process(frame)
                # publicar siempre el frame anotado para UI/visor
                try:
                    self.event_bus.publish("frame", annotated)
                    self.event_bus.publish("frame_processed", None)  # evento para tracing si se necesita
                except Exception:
                    # no queremos que excepciones en subscribers detengan el hilo
                    self.logger.debug("Exception al publicar frame, ignorada.")

                if token:
                    # publicamos el evento principal de detección
                    self.logger.info(f"Detección confirmada: {token}")
                    self.event_bus.publish("detection", token)
                else:
                    # para debug, publicar que no hubo token confirmado
                    self.logger.debug("No se confirmó token en este frame.")

            except Exception as e:
                # registrar error y publicar evento de error para que UI / monitoring lo vea
                self.logger.exception(f"Error procesando frame: {e}")
                try:
                    self.event_bus.publish("processing_error", str(e))
                except Exception:
                    pass

            # ligera pausa para evitar bucle excesivo si hay procesamiento muy rápido
            time.sleep(0.001)

        self.logger.info("ProcessingThread detenido.")

    def stop(self):
        self.logger.info("Stop solicitado en ProcessingThread.")
        self._stop_event.set()

      