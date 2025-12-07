# srlsp-game/src/signperu/core/strategies.py
# Implementación del patrón Strategy para el procesamiento de frames.
# Cada estrategia debe implementar process(frame) -> (token_or_None, annotated_frame)
from abc import ABC, abstractmethod
from collections import deque
from typing import Tuple, Optional

from signperu.core.detector import DetectorSenias
from signperu.core.events import EventBus
from signperu import config

class ProcessingStrategy(ABC):
    """
    Interfaz para estrategias de procesamiento.
    - detector puede ser una instancia de DetectorSenias (wrapper) o similar.
    - event_bus es útil para publicar eventos intermedios.
    - logger es opcional para debug/info.
    """
    def __init__(self, detector: DetectorSenias, event_bus: EventBus = None, logger=None):
        self.detector = detector
        self.event_bus = event_bus
        self.logger = logger

    @abstractmethod
    def process(self, frame) -> Tuple[Optional[str], any]:
        """
        Procesa un frame y devuelve (token_confirmado|None, annotated_frame).
        annotated_frame es el frame con anotaciones (p. ej. para visualizar).
        """
        raise NotImplementedError


class SimpleProcessingStrategy(ProcessingStrategy):
    """
    Estrategia simple que delega en DetectorSenias.predict().
    Usa el suavizado interno del detector (si lo tiene).
    """
    def process(self, frame):
        try:
            token, annotated = self.detector.predict(frame)
            if self.logger:
                self.logger.debug(f"[Strategy:Simple] token={token}")
            # publicar evento raw si se quiere (compatibilidad)
            if self.event_bus:
                self.event_bus.publish("detection_strategy_simple", token)
            return token, annotated
        except Exception as e:
            if self.logger:
                self.logger.exception("[Strategy:Simple] Error procesando frame")
            raise


class TemporalConsensusStrategy(ProcessingStrategy):
    """
    Estrategia que realiza voting/consensus sobre N frames usando la salida
    'cruda' del clasificador interno (si está disponible).
    - Este enfoque es útil si quieres diferenciar entre la lógica de suavizado
      propia del detector y una lógica de consenso más agresiva.
    - Parametrizable: window_size y confirm_threshold (por defecto desde config).
    """
    def __init__(self, detector: DetectorSenias, event_bus: EventBus = None, logger=None,
                 window_size=None, confirm_threshold=None):
        super().__init__(detector, event_bus, logger)
        self.window_size = window_size or config.DETECTOR_SMOOTHING_WINDOW
        self.confirm_threshold = confirm_threshold or config.DETECTOR_CONFIRM_THRESHOLD
        self._buffer = deque(maxlen=self.window_size)

    def _get_raw_prediction(self, frame):
        """
        Intenta usar el clasificador interno (si detector expone _clf).
        Si no está disponible, usar detector.predict() como fallback.
        Retorna (raw_token_or_None, annotated_frame)
        """
        # Si el wrapper DetectorSenias tiene un acceso a la instancia cruda, usarla:
        clf = getattr(self.detector, "_clf", None)
        if clf and hasattr(clf, "procesar_mano"):
            try:
                token, annotated = clf.procesar_mano(frame)
                return token, annotated
            except Exception:
                # Si falla, fallback a predict
                pass

        # fallback si no hay _clf o falló
        return self.detector.predict(frame)

    def process(self, frame):
        try:
            raw_token, annotated = self._get_raw_prediction(frame)
            # encolamos el resultado crudo
            self._buffer.append(raw_token)
            if self.logger:
                self.logger.debug(f"[Strategy:Temporal] buffer={list(self._buffer)}")

            # contar ocurrencias ignorando None
            counts = {}
            for item in self._buffer:
                if item is None:
                    continue
                counts[item] = counts.get(item, 0) + 1

            if not counts:
                # publicar evento de que no hay detección confirmada aún
                if self.event_bus:
                    self.event_bus.publish("detection_strategy_temporal_none", None)
                return None, annotated

            candidato = max(counts, key=counts.get)
            if counts[candidato] >= self.confirm_threshold:
                # confirmamos y vaciamos buffer para evitar repetición inmediata
                self._buffer.clear()
                if self.logger:
                    self.logger.info(f"[Strategy:Temporal] Confirmado: {candidato}")
                if self.event_bus:
                    self.event_bus.publish("detection_strategy_temporal_confirmed", candidato)
                return candidato, annotated

            # aun no hay consenso
            if self.event_bus:
                self.event_bus.publish("detection_strategy_temporal_partial", counts)
            return None, annotated

        except Exception as e:
            if self.logger:
                self.logger.exception("[Strategy:Temporal] Error en processing")
            raise
