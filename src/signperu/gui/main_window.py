#srlsp-game/src/signperu/gui/main_window.py
# Interfaz principal usando CustomTkinter.
# Muestra visor de cámara (frames recibidos por EventBus) y recibe eventos "detection".
#
# Requisitos: customtkinter, pillow, opencv-python, numpy
#
# Diseño:
# - La UI NO manipula frames directamente desde hilos secundarios. Se suscribe al EventBus
#   con callbacks ligeros que colocan frames en una queue thread-safe.
# - El loop de Tk usa after() para consumir la queue y actualizar la imagen en el Label.
# - Botones: Iniciar captura, Detener captura, Seleccionar juego (placeholder), Salir.
# - Muestra un texto con la última detección por unos segundos.

#srlsp-game/src/signperu/gui/main_window.py
import threading
import time
import os
import customtkinter as ctk
from PIL import Image, ImageTk

from queue import Queue
from signperu.core.events import EventBus
from signperu.core.capture import CaptureThread
from signperu.core.processing import ProcessingThread
from signperu.core.detector import DetectorWrapper
from signperu.persistence.db_manager import DBManager

# Importamos las clases de juego (si están disponibles)
try:
    from signperu.games.juego_AH import JuegoAH
except Exception:
    JuegoAH = None

try:
    from signperu.games.juego_lc import JuegoLC
except Exception:
    JuegoLC = None

try:
    from signperu.games.juego_ladrillos import JuegoLadrillos
except Exception:
    JuegoLadrillos = None

CTK_IMG_SIZE = (380, 280)  # tamaño preview cámara en la GUI (ajusta si quieres)

class MainWindow:
    def _init_(self, event_bus: EventBus, db: DBManager, config):
        self.event_bus = event_bus
        self.db = db
        self.config = config

        # hilos/cola (inicialmente no arrancados)
        self.frame_q = None
        self.capture = None
        self.processing = None
        self.detector = None

        # último frame recibido (BGR numpy array)
        self._latest_frame = None
        self._frame_lock = threading.Lock()

        # ventana
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title("SignPeru - Menú Principal")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # GUI layout
        self._build_ui()

        # subscribir a detecciones para mostrar la última letra
        self._last_detected = None
        self.event_bus.subscribe("hand_detected", self._on_hand_detected_event)
        self.event_bus.subscribe("frame_captured", self._on_frame_event)

        # refresco del preview
        self._preview_job = None
        self._running = False

    # ---------------- UI ----------------
    def _build_ui(self):
        w, h = 1000, 700
        self.root.geometry(f"{w}x{h}")

        # Top frame: título + botones control cámara
        top = ctk.CTkFrame(self.root)
        top.pack(fill="x", padx=12, pady=8)

        title = ctk.CTkLabel(top, text="SignPeru - Selección de Juegos", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(side="left", padx=(6,12))

        self.btn_start_cam = ctk.CTkButton(top, text="Iniciar cámara", command=self.start_capture)
        self.btn_start_cam.pack(side="right", padx=6)
        self.btn_stop_cam = ctk.CTkButton(top, text="Detener cámara", command=self.stop_capture, state="disabled")
        self.btn_stop_cam.pack(side="right", padx=6)

        # Middle: cámara preview a la izquierda, opciones a la derecha
        middle = ctk.CTkFrame(self.root)
        middle.pack(fill="both", expand=True, padx=12, pady=8)

        # preview panel
        preview_frame = ctk.CTkFrame(middle, width=CTK_IMG_SIZE[0]+20)
        preview_frame.pack(side="left", fill="y", padx=(0,12))
        preview_frame.pack_propagate(False)

        preview_label = ctk.CTkLabel(preview_frame, text="Preview cámara", font=ctk.CTkFont(size=14))
        preview_label.pack(pady=(6,0))
        self._preview_canvas = ctk.CTkLabel(preview_frame, text="(no camera)", width=CTK_IMG_SIZE[0], height=CTK_IMG_SIZE[1])
        self._preview_canvas.pack(padx=10, pady=6)

        # detección actual
        self.detect_label = ctk.CTkLabel(preview_frame, text="Última detección: —", font=ctk.CTkFont(size=16))
        self.detect_label.pack(pady=(6,0))

        # Right: botones de juegos y consola simple
        right_frame = ctk.CTkFrame(middle)
        right_frame.pack(side="left", fill="both", expand=True)

        games_title = ctk.CTkLabel(right_frame, text="Juegos", font=ctk.CTkFont(size=18, weight="bold"))
        games_title.pack(pady=(6,4))

        # Botones de juegos (se desactivan si el juego no está importable)
        btn_frame = ctk.CTkFrame(right_frame)
        btn_frame.pack(pady=6)

        self.btn_ah = ctk.CTkButton(btn_frame, text="Ahorcado (AH)", width=220, command=lambda: self._launch_game("AH"))
        self.btn_ah.grid(row=0, column=0, padx=8, pady=8)
        if JuegoAH is None:
            self.btn_ah.configure(state="disabled")

        self.btn_lc = ctk.CTkButton(btn_frame, text="Letras Caen (LC)", width=220, command=lambda: self._launch_game("LC"))
        self.btn_lc.grid(row=1, column=0, padx=8, pady=8)
        if JuegoLC is None:
            self.btn_lc.configure(state="disabled")

        self.btn_ladr = ctk.CTkButton(btn_frame, text="Arkanoid (LADRILLOS)", width=220, command=lambda: self._launch_game("LADRILLOS"))
        self.btn_ladr.grid(row=2, column=0, padx=8, pady=8)
        if JuegoLadrillos is None:
            self.btn_ladr.configure(state="disabled")

        # Consola / log simple
        console_title = ctk.CTkLabel(right_frame, text="Consola", font=ctk.CTkFont(size=14))
        console_title.pack(pady=(12,2))
        self.console = ctk.CTkTextbox(right_frame, width=420, height=260)
        self.console.pack(padx=8, pady=6)

        # Footer: cerrar app
        bottom = ctk.CTkFrame(self.root)
        bottom.pack(fill="x", padx=12, pady=8)
        self.btn_quit = ctk.CTkButton(bottom, text="Cerrar aplicación", fg_color="red", command=self._on_close)
        self.btn_quit.pack(side="right", padx=6)

    # ---------------- EventBus handlers ----------------
    def _on_frame_event(self, frame):
        with self._frame_lock:
            self._latest_frame = frame

    def _on_hand_detected_event(self, *args, **kwargs):
        # buscamos primer string en args/kwargs
        letra = None
        for a in args:
            if isinstance(a, str):
                letra = a
                break
        if letra is None:
            for key in ("letra","letter","detected","result"):
                v = kwargs.get(key)
                if isinstance(v, str):
                    letra = v
                    break
        if letra:
            self._last_detected = letra
            self._append_console(f"Detección: {letra}")
            # actualizar etiqueta en hilo principal
            try:
                self.detect_label.configure(text=f"Última detección: {letra}")
            except Exception:
                pass

    # ---------------- capture / processing control ----------------
    def start_capture(self):
        """Inicia capture + processing si no están corriendo."""
        if self.capture and getattr(self.capture, "running", False):
            return
        self._append_console("Iniciando captura y procesamiento...")
        # crear resources
        self.frame_q = Queue(maxsize=2)
        self.capture = CaptureThread(self.event_bus, src=self.config.CAMERA_SRC, target_fps=self.config.FPS, frame_queue=self.frame_q)
        self.detector = DetectorWrapper()
        self.processing = ProcessingThread(self.event_bus, self.detector, self.frame_q)

        # start threads
        self.capture.start()
        self.processing.start()
        self.btn_start_cam.configure(state="disabled")
        self.btn_stop_cam.configure(state="normal")
        self._running = True
        # start preview only when capture started
        self._schedule_preview()
        self._append_console("Cámara iniciada.")

    def stop_capture(self):
        """Detiene capture + processing y cancela preview."""
        self._append_console("Deteniendo captura y procesamiento...")
        try:
            if self.capture:
                self.capture.stop()
        except Exception:
            pass
        try:
            if self.processing:
                self.processing.stop()
        except Exception:
            pass
        self.btn_start_cam.configure(state="normal")
        self.btn_stop_cam.configure(state="disabled")
        self._running = False
        # cancelar preview
        if self._preview_job:
            try:
                self.root.after_cancel(self._preview_job)
            except Exception:
                pass
        self._preview_job = None
        self._append_console("Cámara detenida.")

    # ---------------- preview drawing ----------------
    def _schedule_preview(self):
        # solo programar si capture está corriendo
        if not getattr(self.capture, "running", False):
            return
        if self._preview_job:
            return
        self._preview_job = self.root.after(50, self._update_preview)

    def _update_preview(self):
        # obtiene último frame y lo pinta en el widget
        frame = None
        with self._frame_lock:
            if self._latest_frame is not None:
                frame = self._latest_frame.copy()

        if frame is not None:
            try:
                import cv2
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                img.thumbnail(CTK_IMG_SIZE, Image.LANCZOS)
                imgtk = ImageTk.PhotoImage(img)
                self._preview_canvas.configure(image=imgtk, text="")
                # debemos mantener referencia para evitar GC
                self._preview_canvas.image = imgtk
            except Exception:
                pass
        else:
            # mostrar texto cuando no hay frame
            self._preview_canvas.configure(text="(sin frames)")

        # reprogramar sólo si seguimos corriendo y la ventana visible
        if self._running and self.root.state() != "withdrawn":
            self._preview_job = self.root.after(50, self._update_preview)
        else:
            self._preview_job = None

    # ---------------- launching games ----------------
    def _wait_for_first_frame(self, timeout: float = 3.0) -> bool:
        """
        Espera hasta timeout segundos a que self._latest_frame no sea None.
        Devuelve True si apareció al menos un frame, False si timeout.
        Esto evita lanzar un juego antes de que la cámara/detector estén listos.
        """
        start = time.time()
        while time.time() - start < timeout:
            with self._frame_lock:
                if self._latest_frame is not None:
                    return True
            time.sleep(0.08)
        return False

    def _launch_game(self, key: str):
        """
        Lanza el juego correspondiente.
        Mejoras:
        - Si la cámara no está activa la inicia y espera a primer frame (timeout).
        - Oculta la ventana principal (withdraw) pero no destruye capture threads.
        - Tras finalizar el juego intenta detener el juego con stop() y, si
          fuimos quienes arrancamos la cámara, la para.
        """
        mapping = {
            "AH": JuegoAH,
            "LC": JuegoLC,
            "LADRILLOS": JuegoLadrillos,
        }
        cls = mapping.get(key)
        if cls is None:
            self._append_console(f"Juego {key} no disponible.")
            return

        started_here = False
        try:
            if not (self.capture and getattr(self.capture, "running", False)):
                self._append_console("La cámara no está activa. Iniciando automáticamente...")
                self.start_capture()
                started_here = True
                # Esperamos a que aparezca el primer frame (o timeout)
                ready = self._wait_for_first_frame(timeout=4.0)
                if not ready:
                    self._append_console("Advertencia: no se recibió frame en el tiempo esperado (4s). El detector puede tardar más en cargar.")
                else:
                    self._append_console("Primer frame recibido. Lanzando juego.")
        except Exception as e:
            self._append_console(f"Error iniciando cámara: {e}")

        # deshabilitar botones para evitar re-entradas
        self._set_games_buttons_state("disabled")
        self._append_console(f"Lanzando juego: {key}")

        # ocultar ventana principal para evitar solapamientos y liberar focus
        try:
            # pausamos preview visualmente, pero no matamos threads inmediatamente
            if self._preview_job:
                try:
                    self.root.after_cancel(self._preview_job)
                except Exception:
                    pass
                self._preview_job = None
            self.root.withdraw()
        except Exception:
            pass

        game = None
        try:
            game = cls(event_bus=self.event_bus, db=self.db, config=self.config, user=None)
            # start() es bloqueante — cuando termine vuelve aquí
            game.start()
            self._append_console(f"Juego {key} finalizó correctamente.")
        except Exception as ex:
            self._append_console(f"Error ejecutando juego {key}: {ex}")
        finally:
            # Intentamos parar limpiamente el juego si provee stop()
            try:
                if game:
                    game.stop()
            except Exception:
                pass

            # Si fuimos quienes arrancamos la cámara, la detenemos
            try:
                if started_here:
                    self.stop_capture()
            except Exception:
                pass

            # Reactivar botones
            self._set_games_buttons_state("normal")

            # Reaparecer la ventana principal
            try:
                self.root.deiconify()
            except Exception:
                pass

            # Restaurar preview si capture sigue corriendo
            if getattr(self.capture, "running", False):
                self._schedule_preview()

            # Mostrar último valor detectado
            if self._last_detected:
                try:
                    self.detect_label.configure(text=f"Última detección: {self._last_detected}")
                except Exception:
                    pass

            self._append_console("Volvimos al menú principal.")


    def _set_games_buttons_state(self, state="normal"):
        if JuegoAH is not None:
            self.btn_ah.configure(state=state)
        if JuegoLC is not None:
            self.btn_lc.configure(state=state)
        if JuegoLadrillos is not None:
            self.btn_ladr.configure(state=state)

    # ---------------- console ----------------
    def _append_console(self, text):
        try:
            stamp = time.strftime("%H:%M:%S")
            self.console.insert(ctk.END, f"[{stamp}] {text}\n")
            self.console.see(ctk.END)
        except Exception:
            print(text)

    # ---------------- close ----------------
    def _on_close(self):
        self._append_console("Cerrando aplicación...")
        # detener hilos
        self.stop_capture()
        # desuscribir
        try:
            self.event_bus.unsubscribe("frame_captured", self._on_frame_event)
            self.event_bus.unsubscribe("hand_detected", self._on_hand_detected_event)
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    # ---------------- start loop ----------------
    def run(self):
        # start mainloop
        self.root.mainloop()