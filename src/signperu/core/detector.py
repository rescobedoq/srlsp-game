# srlsp-game/src/signperu/core/detector.py
# Wrapper alrededor de abecedario.ClasificadorSenia
# Provee una API sencilla: predict(frame) -> token|None y smoothing temporal

from collections import deque
from signperu.clasificador.abecedario import ClasificadorSenia
from signperu import config

class DetectorSenias:
    def __init__(self, smoothing_window=None, confirm_threshold=None):
        # instanciamos el clasificador que ya viene en abecedario.py
        self._clf = ClasificadorSenia()
        # parámetros de suavizado y confirmación
        self.smoothing_window = smoothing_window or config.DETECTOR_SMOOTHING_WINDOW
        self.confirm_threshold = confirm_threshold or config.DETECTOR_CONFIRM_THRESHOLD
        # buffer circular para las últimas detecciones
        self._buffer = deque(maxlen=self.smoothing_window)

    def predict(self, frame):
        """
        Procesa un frame y devuelve:
         - Una letra (string) si hay detección confirmada
         - None si no hay detección o no se confirmó por el suavizado
        NOTA: usa internamente ClasificadorSenia.procesar_mano
        """
        letra, annotated_frame = self._clf.procesar_mano(frame)
        # añadimos al buffer (puede ser None)
        self._buffer.append(letra)
        # contamos la frecuencia del valor más común en la ventana
        # confirmamos solo si aparece >= confirm_threshold y no es None
        if not self._buffer:
            return None, annotated_frame

        # hallar candidato más frecuente
        counts = {}
        for item in self._buffer:
            if item is None: 
                continue
            counts[item] = counts.get(item, 0) + 1

        if not counts:
            return None, annotated_frame

        # candidato y su cuenta
        candidato = max(counts, key=counts.get)
        if counts[candidato] >= self.confirm_threshold:
            # vaciamos buffer para evitar repetición inmediata
            self._buffer.clear()
            return candidato, annotated_frame

        return None, annotated_frame
