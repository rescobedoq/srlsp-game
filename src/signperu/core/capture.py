# srlsp-game/src/signperu/core/capture.py
# Captura frames de la cámara en un hilo y los pone en una queue (thread-safe)
import cv2
import threading
import time
from queue import Queue, Empty
from signperu import config

class CaptureThread(threading.Thread):
    def __init__(self, frame_queue: Queue, camera_index=None, width=None, height=None, target_fps=None):
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.camera_index = camera_index if camera_index is not None else config.CAMERA_INDEX
        self.width = width or config.FRAME_WIDTH
        self.height = height or config.FRAME_HEIGHT
        self.target_fps = target_fps or config.TARGET_FPS
        self._stop_event = threading.Event()
        self._cap = None

    def run(self):
        # inicializar la captura
        self._cap = cv2.VideoCapture(self.camera_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        # cálculo de espera entre frames
        delay = 1.0 / float(self.target_fps) if self.target_fps > 0 else 0
        while not self._stop_event.is_set():
            ret, frame = self._cap.read()
            if not ret:
                # breve espera y retry
                time.sleep(0.05)
                continue
            # colocamos el frame en la cola (si está llena, descartamos el más antiguo)
            try:
                self.frame_queue.put(frame, block=False)
            except Exception:
                # si la cola está llena, tratamos de vaciar uno y reintentar
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put(frame, block=False)
                except Exception:
                    pass
            time.sleep(delay)

        # liberamos recursos
        if self._cap and self._cap.isOpened():
            self._cap.release()

    def stop(self):
        self._stop_event.set()
