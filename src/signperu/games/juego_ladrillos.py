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
VIDEO_POS = (10, 20)  # si canvas width = 800
#Offset horizontal desde la izquierda para pintar el área del juego (separa del panel cámara)
GAME_OFFSET = VIDEO_W + 30   # espacio entre panel de cámara y área de juego
# Tamaños del canvas general
CANVAS_W = 1100
CANVAS_H = 700

class JuegoLadrillos(GameBase):
    def __init__(self, event_bus, db=None, config=None, user=None):
        super().__init__(event_bus, db, config, user)
        self.width = CANVAS_W
        self.height = CANVAS_H
        # logic se creará en start() con dimensiones del área de juego
        self.logic = None
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

        # calcular área de juego (dentro de la ventana) y crear la lógica con esas dimensiones
        game_area_w = max(400, self.width - GAME_OFFSET - 40)   # mínimo 400 para que quepan bloques
        game_area_h = max(400, self.height - 60)
        # instanciar lógica (coordenadas y límites dentro del área de juego)
        self.logic = ClaseLadrillos(width=game_area_w, height=game_area_h)

        self._show_main_menu()
        self.root.mainloop()

    def _show_main_menu(self):
        self.canvas.delete("all")
        # dibujar fondo cámara + placeholder video area
        vx, vy = VIDEO_POS
        self.canvas.create_rectangle(vx-2, vy-2, vx+VIDEO_W+2, vy+VIDEO_H+2, outline="white", tags="video_frame_bg")
        # Opcional: mini-preview del fondo del área de juego
        game_cx = GAME_OFFSET + (self.logic.width // 2)
        game_cy = self.height // 2

        logo_path = os.path.join(MEDIA_DIR, "arkanoid.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                # ajusta tamaño para caber en el area de juego
                max_logo_w = min(400, self.logic.width - 40)
                new_h = int(max_logo_w * img.height / img.width)
                img = img.resize((max_logo_w, new_h), Image.LANCZOS)
                self._bg_photo = ImageTk.PhotoImage(img)
                self.canvas.create_image(GAME_OFFSET + self.logic.width//2, self.height//2 - 120, image=self._bg_photo)
            except Exception:
                pass

        # botones centrados en el area de juego
        btn_start = ttk.Button(self.root, text="Empezar", style="Custom.TButton", command=lambda: self._start_game(1))
        btn_how = ttk.Button(self.root, text="Cómo jugar", style="Custom.TButton", command=self._show_how_to)
        btn_exit = ttk.Button(self.root, text="Salir", style="Custom.TButton", command=self._on_close)

        # crear ventanas del canvas colocadas centradas en el área de juego
        center_x = GAME_OFFSET + self.logic.width//2
        self.canvas.create_window(center_x, self.height//2 - 10, window=btn_start)
        self.canvas.create_window(center_x, self.height//2 + 30, window=btn_how)
        self.canvas.create_window(center_x, self.height//2 + 70, window=btn_exit)

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
        # Dibujar bloques con offset en X
        for rect in st["blocks"]:
            x1,y1,x2,y2 = rect
            self.canvas.create_rectangle(x1 + GAME_OFFSET, y1, x2 + GAME_OFFSET, y2,
                                         fill="skyblue", outline="white", tags="block")
        px, py, pw, ph = st["paddle"]
        # paleta con offset en X
        self._paddle_item = self.canvas.create_rectangle(
            px - pw//2 + GAME_OFFSET, py - ph//2,
            px + pw//2 + GAME_OFFSET, py + ph//2,
            fill="white", tags="paddle")
        bx, by, br = st["ball"]
        # bola con offset en X
        self._ball_item = self.canvas.create_oval(
            bx - br + GAME_OFFSET, by - br,
            bx + br + GAME_OFFSET, by + br,
            fill="red", tags="ball")
        # HUD: puntuación a la izquierda del área, vidas a la derecha dentro del area de juego
        self.canvas.create_text(GAME_OFFSET + 10, 10, anchor="nw", text=f"Puntuación: {st['score']}", fill="white", font=("Arial", 14), tags="hud")
        self.canvas.create_text(GAME_OFFSET + self.logic.width - 110, 10, anchor="nw", text=f"Vidas: {st['lives']}", fill="white", font=("Arial", 14), tags="hud")

        # reservar área donde se pintará el video (panel dentro del canvas)
        vx, vy = VIDEO_POS
        self.canvas.create_rectangle(vx-2, vy-2, vx+VIDEO_W+2, vy+VIDEO_H+2, outline="white", tags="video_frame_bg")
        self._video_area_pos = (vx, vy)

    def _schedule_next_frame(self):
        self._job = self.root.after(20, self._game_loop)

    def _game_loop(self):
        # actualizar lógica
        self.logic.step()
        st = self.logic.get_state()

        # actualizar video panel (si hay frame)
        self._draw_video_panel()

        # redibujar bloques (simplificación: redibujamos todos) con offset
        self.canvas.delete("block")
        for rect in st["blocks"]:
            x1,y1,x2,y2 = rect
            self.canvas.create_rectangle(x1 + GAME_OFFSET, y1, x2 + GAME_OFFSET, y2, fill="skyblue", outline="white", tags="block")

        # paleta y bola con offset en X
        px, py, pw, ph = st["paddle"]
        self.canvas.coords(self._paddle_item,
                           px - pw//2 + GAME_OFFSET, py - ph//2,
                           px + pw//2 + GAME_OFFSET, py + ph//2)
        bx, by, br = st["ball"]
        self.canvas.coords(self._ball_item,
                           bx - br + GAME_OFFSET, by - br,
                           bx + br + GAME_OFFSET, by + br)

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
    
        # ------------------ implementaciones obligatorias (GameBase) ------------------
    def on_hand_detected(self, letra, frame=None):
        """
        Implementación de la interfaz GameBase.
        Puede ser llamada desde otros hilos; delegamos en el handler existente.
        """
        # delegar a nuestro handler robusto (acepta *args/**kwargs)
        try:
            # si viene desde hilo externo, reutilizamos el mismo flujo
            self._on_hand_detected_event(letra, frame=frame)
        except Exception:
            # proteger contra errores en hilos externos
            pass

    def stop(self):
        """
        Parada ordenada: cancela el after loop, desuscribe handlers y cierra la ventana.
        Puede llamarse desde el thread principal al cerrar la app o desde app.py.
        """
        # detener el loop scheduled
        if getattr(self, "_job", None):
            try:
                self.root.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

        # desuscribir handlers (seguro aunque ya lo hagas en _on_close)
        try:
            self.event_bus.unsubscribe("frame_captured", self._on_frame_event)
        except Exception:
            pass
        try:
            self.event_bus.unsubscribe("hand_detected", self._on_hand_detected_event)
        except Exception:
            pass

        # destruir ventana si existe
        try:
            if self.root:
                self.root.destroy()
        except Exception:
            pass

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

