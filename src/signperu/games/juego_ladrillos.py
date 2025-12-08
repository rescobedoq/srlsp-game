#srlsp-game/src/signperu/games/juego_ladrillos.py
"""
UI Tkinter para Arkanoid (usa ClaseLadrillos para la lógica).
Feed de cámara integrado en la misma ventana (panel dentro del Canvas).
Se integra con EventBus: subscribe 'frame_captured' y 'hand_detected'.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
import os

from signperu.games.game_base import GameBase
from signperu.games.clase_ladrillos import ClaseLadrillos

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "RecursosMultimedia")

# Video panel size (ajusta aquí)
VIDEO_W = 380
VIDEO_H = 290
# Posición (X,Y) relativa al canvas (colocado a la derecha superior)
VIDEO_POS = (800 - VIDEO_W - 10, 20)  # si canvas width = 800

class JuegoLadrillos(GameBase):
    def __init__(self, event_bus, db=None, config=None, user=None):
        super().__init__(event_bus, db, config, user)
        self.width = 800
        self.height = 600
        self.logic = ClaseLadrillos(width=self.width, height=self.height)

        # UI
        self.root = None
        self.canvas = None
        self._bg_photo = None

        # frame recibido por EventBus
        self._frame_lock = threading.Lock()
        self._latest_frame = None  # BGR numpy array
        self._video_imgtk = None   # referencia ImageTk para evitar GC

        # suscripciones (flexible con *args, **kwargs)
        self.event_bus.subscribe("frame_captured", self._on_frame_event)
        self.event_bus.subscribe("hand_detected", self._on_hand_detected_event)

        self._job = None

    # ---------- EventBus handlers ----------
    def _on_frame_event(self, frame):
        # recibe frames BGR desde CaptureThread/ProcessingThread
        with self._frame_lock:
            self._latest_frame = frame

    def _on_hand_detected_event(self, *args, **kwargs):
        letra = None
        for a in args:
            if isinstance(a, str):
                letra = a
                break
        if letra is None:
            for k in ("letra","letter","detected","result"):
                v = kwargs.get(k)
                if isinstance(v, str):
                    letra = v
                    break
        if letra:
            self.logic.process_detection(letra)

    # ---------- UI lifecycle ----------
    def start(self):
        self.root = tk.Tk()
        self.root.title("Arkanoid - Señales")
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        style = ttk.Style()
        style.configure("Custom.TButton", font=("Arial", 12, "bold"))

        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._show_main_menu()
        self.root.mainloop()

    def _show_main_menu(self):
        self.canvas.delete("all")
        logo_path = os.path.join(MEDIA_DIR, "arkanoid.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img = img.resize((400, int(400 * img.height / img.width)), Image.LANCZOS)
                self._bg_photo = ImageTk.PhotoImage(img)
                self.canvas.create_image(self.width//2, self.height//2 - 120, image=self._bg_photo)
            except Exception:
                pass

        btn_start = ttk.Button(self.root, text="Empezar", style="Custom.TButton", command=lambda: self._start_game(1))
        btn_how = ttk.Button(self.root, text="Cómo jugar", style="Custom.TButton", command=self._show_how_to)
        btn_exit = ttk.Button(self.root, text="Salir", style="Custom.TButton", command=self._on_close)

        self.canvas.create_window(self.width//2, self.height//2 - 10, window=btn_start)
        self.canvas.create_window(self.width//2, self.height//2 + 30, window=btn_how)
        self.canvas.create_window(self.width//2, self.height//2 + 70, window=btn_exit)

    def _show_how_to(self):
        self.canvas.delete("all")
        self.canvas.create_text(self.width//2, self.height//2 - 30, text="Mueve la paleta con señas:\n'A' izquierda, 'B' derecha",
                                fill="white", font=("Arial", 18))
        btn_back = ttk.Button(self.root, text="Volver", command=self._show_main_menu)
        self.canvas.create_window(self.width//2, self.height//2 + 60, window=btn_back)

    # ---------- game start/loop/draw ----------
    def _start_game(self, level:int):
        self.logic.reset(level=level)
        # fondo si existe
        bg_path = os.path.join(MEDIA_DIR, "wood.png")
        if os.path.exists(bg_path):
            try:
                bg = Image.open(bg_path).resize((self.width, self.height), Image.LANCZOS)
                self._bg_photo = ImageTk.PhotoImage(bg)
                self.canvas.create_image(0,0, anchor=tk.NW, image=self._bg_photo)
            except Exception:
                self.canvas.configure(bg="black")
        else:
            self.canvas.configure(bg="black")

        # crear objetos iniciales del juego
        self._create_draw_items()
        # iniciar loop con after (no bloqueante)
        self._schedule_next_frame()

    def _create_draw_items(self):
        self.canvas.delete("block")
        self.canvas.delete("paddle")
        self.canvas.delete("ball")
        self.canvas.delete("hud")
        st = self.logic.get_state()
        for rect in st["blocks"]:
            x1,y1,x2,y2 = rect
            self.canvas.create_rectangle(x1,y1,x2,y2, fill="skyblue", outline="white", tags="block")
        px, py, pw, ph = st["paddle"]
        self._paddle_item = self.canvas.create_rectangle(px - pw//2, py - ph//2,
                                                         px + pw//2, py + ph//2,
                                                         fill="white", tags="paddle")
        bx, by, br = st["ball"]
        self._ball_item = self.canvas.create_oval(bx-br, by-br, bx+br, by+br, fill="red", tags="ball")
        self.canvas.create_text(10, 10, anchor="nw", text=f"Puntuación: {st['score']}", fill="white", font=("Arial", 14), tags="hud")
        self.canvas.create_text(self.width - 110, 10, anchor="nw", text=f"Vidas: {st['lives']}", fill="white", font=("Arial", 14), tags="hud")

        # reservar área donde se pintará el video (panel dentro del canvas)
        vx, vy = VIDEO_POS
        # dibujamos un rectángulo de fondo y un placeholder image id (se actualizará)
        self.canvas.create_rectangle(vx-2, vy-2, vx+VIDEO_W+2, vy+VIDEO_H+2, outline="white", tags="video_frame_bg")
        # guardamos posición para el draw
        self._video_area_pos = (vx, vy)

    def _schedule_next_frame(self):
        self._job = self.root.after(20, self._game_loop)

    def _game_loop(self):
        # actualizar lógica
        self.logic.step()
        st = self.logic.get_state()

        # actualizar video panel (si hay frame)
        self._draw_video_panel()

        # redibujar bloques (simplificación: redibujamos todos)
        self.canvas.delete("block")
        for rect in st["blocks"]:
            x1,y1,x2,y2 = rect
            self.canvas.create_rectangle(x1,y1,x2,y2, fill="skyblue", outline="white", tags="block")

        # paleta y bola
        px, py, pw, ph = st["paddle"]
        self.canvas.coords(self._paddle_item, px - pw//2, py - ph//2, px + pw//2, py + ph//2)
        bx, by, br = st["ball"]
        self.canvas.coords(self._ball_item, bx-br, by-br, bx+br, by+br)

        # HUD
        self.canvas.delete("hud")
        self.canvas.create_text(10, 10, anchor="nw", text=f"Puntuación: {st['score']}", fill="white", font=("Arial", 14), tags="hud")
        self.canvas.create_text(self.width - 110, 10, anchor="nw", text=f"Vidas: {st['lives']}", fill="white", font=("Arial", 14), tags="hud")

        # comprobar fin de juego
        if not st["in_play"]:
            try:
                self.save_score(st["score"], game_name="JuegoLadrillos")
            except Exception:
                pass
            msg = "Ganaste!" if not st["blocks"] else "Perdiste"
            self.canvas.create_text(self.width//2, self.height//2, text=msg, fill="white", font=("Arial", 32), tags="hud")
            return self.root.after(1500, self._back_to_menu)

        # continuar loop
        self._schedule_next_frame()

    def _draw_video_panel(self):
        # Dibuja el último frame (si existe) en el área reservada dentro del canvas.
        if not hasattr(self, "_video_area_pos"):
            return
        vx, vy = self._video_area_pos

        frame = None
        with self._frame_lock:
            if self._latest_frame is not None:
                frame = self._latest_frame.copy()
        if frame is None:
            # si no hay frame, pintar fondo oscuro en la zona
            self.canvas.create_rectangle(vx, vy, vx+VIDEO_W, vy+VIDEO_H, fill="#141414", tags="video_frame")
            return

        try:
            import cv2
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img = img.resize((VIDEO_W, VIDEO_H), Image.LANCZOS)

            # crear PhotoImage y colocarlo en canvas; mantener referencia en self._video_imgtk
            self._video_imgtk = ImageTk.PhotoImage(img)
            # si ya existe un item de imagen lo reemplazamos; usamos tag "video_frame_img"
            existing = self.canvas.find_withtag("video_frame_img")
            if existing:
                self.canvas.itemconfigure(existing[0], image=self._video_imgtk)
            else:
                # create_window no es necesario: ponemos image en canvas con create_image
                self.canvas.create_image(vx, vy, anchor=tk.NW, image=self._video_imgtk, tags="video_frame_img")
        except Exception:
            # en caso de error (p. ej. conversión), rellenar con rect
            self.canvas.create_rectangle(vx, vy, vx+VIDEO_W, vy+VIDEO_H, fill="#141414", tags="video_frame")

    def _back_to_menu(self):
        self.canvas.delete("all")
        self._show_main_menu()

    # ---------- cierre ----------
    def _on_close(self):
        if self._job:
            try:
                self.root.after_cancel(self._job)
            except Exception:
                pass
        try:
            self.event_bus.unsubscribe("frame_captured", self._on_frame_event)
            self.event_bus.unsubscribe("hand_detected", self._on_hand_detected_event)
        except Exception:
            pass
        try:
            if self.root:
                self.root.destroy()
        except Exception:
            pass

