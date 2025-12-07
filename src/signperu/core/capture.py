# srlsp-game/src/signperu/core/capture.py
# Captura frames de la cámara en un hilo y los pone en una queue (thread-safe)
import cv2
import threading
import time
from queue import Queue, Empty
from queue import Queue, Full

class CaptureThread(threading.Thread):
    """
    Lector de cámara en un hilo. Publica frames por event_bus y también los pone en frame_queue.
    """
    def __init__(self, event_bus, src=0, target_fps=20, frame_queue:Queue=None):
        super().__init__(daemon=True)
        self.src = src
        self.cap = None
        self.running = False
        self.event_bus = event_bus
        self.target_fps = target_fps
        self.frame_queue = frame_queue or Queue(maxsize=2)

    def run(self):
        # inicializar la captura
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0)
        if not self.cap.isOpened():
            print("[CaptureThread] No se pudo abrir la cámara")
            return
        self.running = True
        interval = 1.0 / max(1, self.target_fps)
        while self.running:
            t0 = time.time()
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            # publicamos frame en cola (para procesamiento) y en bus (para GUI si desea)
            try:
                # non-blocking put: si cola llena, descartamos el frame anterior
                self.frame_queue.put(frame, block=False)
            except Full:
                try:
                    _ = self.frame_queue.get_nowait() # si la cola está llena, tratamos de vaciar uno y reintentar 
                    self.frame_queue.put(frame, block=False)
                except Exception:
                    pass
            # publicar por bus (opcional)
            self.event_bus.publish("frame_captured", frame)
            dt = time.time() - t0
            sleep = interval - dt
            if sleep > 0:
                time.sleep(sleep)

    def stop(self):
        self.running = False
        try:
            if self.cap and self.cap.isOpened(): # liberamos recursos
                self.cap.release()
        except Exception:
            pass

