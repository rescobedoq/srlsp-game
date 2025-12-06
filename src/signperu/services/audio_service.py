#src/signperu/services/audio_service.py
import threading
import pyttsx3

class AudioService:
    def __init__(self):
        self._engine = pyttsx3.init()
        self._lock = threading.Lock()

    def say(self, text):
        def _job(t):
            with self._lock:
                self._engine.say(t)
                self._engine.runAndWait()
        threading.Thread(target=_job, args=(text,), daemon=True).start()
