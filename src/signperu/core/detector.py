# srlsp-game/src/signperu/core/detector.py
# Wrapper alrededor de abecedario.ClasificadorSenia
# Provee una API sencilla: predict(frame) -> token|None y smoothing temporal
from signperu.clasificador.abecedario import ClasificadorSenia

class DetectorWrapper:
    """
    Wrapper para el clasificador existente en abecedario.py.
    Expone detect_from_frame(frame) -> (letra_detectada | None, annotated_frame)
    """
    def __init__(self, config=None):
        self.config = config or {}
        # Usa la clase existente sin modificarla
        self._clf = ClasificadorSenia()

    def detect_from_frame(self, frame):
        """
        Llama a ClasificadorSenia.procesar_mano(frame) que devuelve (letra, frame_annotado)
        Retorna (letra, frame_annotado)
        """
        try:
            letra, frame_proc, coords = self._clf.procesar_mano(frame)
            return letra, frame_proc, coords
        except Exception as e:
            # Si algo falla, devolvemos None y el frame original
            # para no romper el hilo de procesamiento
            # print("DetectorWrapper error:", e)
            return None, frame, None
