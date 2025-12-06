#srlsp-game/src/signperu/gui/main_window.py
"""A minimal GUI using CustomTkinter that starts/stops the Recognizer and launches games."""
import threading, queue
try:
    import customtkinter as ctk
except Exception:
    ctk = None

from ..core.recognizer import Recognizer
from ..core.matcher import HeuristicMatcher
from ..patterns import abecedario
from ..games.factory import GameFactory
from ..data.db import DB

class MainWindow:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.matcher = HeuristicMatcher(patterns=abecedario.get_patterns())
        self.recognizer = Recognizer(self.event_queue, self.matcher)
        self.db = DB.get_instance()
        self.active_game = None

    def run(self):
        if ctk is None:
            print("CustomTkinter not installed — launching headless demo.")
            print("Start recognizer for 5 seconds demo...")
            self.recognizer.start()
            try:
                import time
                time.sleep(5)
            finally:
                self.recognizer.stop()
            print("Demo finished.")
            return

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")
        root = ctk.CTk()
        root.title("ProyectoTO - SignPeru")
        root.geometry("800x600")

        frame = ctk.CTkFrame(root, padx=20, pady=20)
        frame.pack(fill='both', expand=True)

        btn_start = ctk.CTkButton(frame, text="Iniciar Reconocedor", command=self._start_recognizer)
        btn_start.pack(pady=8)
        btn_stop = ctk.CTkButton(frame, text="Detener Reconocedor", command=self._stop_recognizer)
        btn_stop.pack(pady=8)

        btn_ah = ctk.CTkButton(frame, text="Jugar AH", command=lambda: self._start_game('AH'))
        btn_ah.pack(pady=8)

        root.mainloop()

    def _start_recognizer(self):
        if not self.recognizer.is_alive():
            self.recognizer.start()
            print("Recognizer started")

    def _stop_recognizer(self):
        self.recognizer.stop()
        print("Recognizer stopped")

    def _start_game(self, game_id):
        if self.active_game:
            self.active_game.stop()
        self.active_game = GameFactory.create(game_id, user='demo', event_queue=self.event_queue, db=self.db)
        self.active_game.start()
