#src/signperu/core/recognizer.py
"""Reconocedor en subprocesos que captura fotogramas"""
import threading
import time
import queue
import cv2

try:
    import mediapipe as mp
except Exception:
    mp = None  # allow import even if mediapipe is not installed in this environment

from ..patterns import abecedario
from .features import extract_features

class Recognizer(threading.Thread):
    """Threaded recognizer that captures frames, extracts features and matches to patterns.
    Publishes events to an event_queue (dictionary messages).
    """
    def __init__(self, event_queue: queue.Queue, matcher, camera_index=0, fps=20):
        super().__init__(daemon=True)
        self.event_queue = event_queue
        self.matcher = matcher
        self.camera_index = camera_index
        self.fps = fps
        self._running = threading.Event()
        self._running.set()
        self._mp_hands = mp.solutions.hands.Hands(max_num_hands=1) if mp else None

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        interval = 1.0 / float(self.fps)
        while self._running.is_set():
            ret, frame = cap.read()
            if not ret:
                time.sleep(interval)
                continue

            if self._mp_hands:
                # Convert and process
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self._mp_hands.process(rgb)
                if results.multi_hand_landmarks:
                    lm = results.multi_hand_landmarks[0]
                    vec = extract_features(lm)
                    letra, score = self.matcher.match(vec)
                    self.event_queue.put({'type': 'letter', 'letter': letra, 'score': score})
            else:
                # Fallback: do nothing but wait
                time.sleep(interval)

            time.sleep(interval)

        cap.release()

    def stop(self):
        self._running.clear()
