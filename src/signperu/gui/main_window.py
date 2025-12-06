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

import threading
import time
from queue import Queue, Empty
import cv2
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk

# import de componentes del proyecto
from signperu.core.events import EventBus
from signperu.core.capture import CaptureThread
from signperu.core.processing import ProcessingThread
from signperu.persistence.db_manager import DBManager
from signperu import config

# Tamaños por defecto para la ventana
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
VISOR_WIDTH = 640
VISOR_HEIGHT = 480

class MainWindow(ctk.CTk):
    def __init__(self,
                 event_bus: EventBus = None,
                 frame_queue: Queue = None,
                 capture_thread: CaptureThread = None,
                 processing_thread: ProcessingThread = None,
                 db: DBManager = None,
                 user: dict = None):
        """
        event_bus: instancia compartida de EventBus (si None, se crea una nueva)
        frame_queue: queue de frames (si None, se crea con tamaño por defecto)
        capture_thread / processing_thread: instancias opcionales (si None se crearán al iniciar)
        db: instancia DBManager (si None se inicializa)
        user: diccionario con info del usuario actual (opcional)
        """
        super().__init__()

        # --- dependencias / contexto ---
        self.event_bus = event_bus or EventBus()
        self.frame_queue = frame_queue or Queue(maxsize=4)
        self.capture_thread = capture_thread  # pueden ser None inicialmente
        self.processing_thread = processing_thread
        self.db = db or DBManager()
        self.user = user

        # Queues internas para comunicación segura entre hilos y Tk
        self._ui_frame_queue = Queue(maxsize=2)      # recibe frames desde EventBus
        self._detection_queue = Queue(maxsize=8)     # recibe tokens de detección

        # Variables UI
        self._photo_image = None
        self._last_detection_ts = 0
        self._detection_display_seconds = 2.5

        # Estado
        self._running = False

        # Configuración de la ventana (customtkinter)
        ctk.set_appearance_mode("System")   # "dark"/"light"/"system"
        ctk.set_default_color_theme("blue") # tema
        self.title("ProyectoTO_senias — SignPeru")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Layout: sidebar izquierdo y panel central con visor + controles
        self._create_widgets()

        # Suscripción segura a EventBus
        # IMPORTANTE: los callbacks de EventBus deben ser ligeros y sólo encolar datos.
        self.event_bus.subscribe("frame", self._enqueue_frame_from_eventbus)
        self.event_bus.subscribe("detection", self._enqueue_detection_from_eventbus)
        self.event_bus.subscribe("quit", lambda _: self._on_close())

        # Iniciar polling del UI (after)
        self._schedule_ui_update()

    # -----------------------
    # Creación de widgets
    # -----------------------
    def _create_widgets(self):
        # Frame lateral (sidebar)
        self.sidebar = ctk.CTkFrame(self, width=240)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        # Título / usuario
        self.lbl_app_title = ctk.CTkLabel(self.sidebar, text="SignPeru", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_app_title.pack(pady=(8, 6))

        user_text = self.user["username"] if self.user and "username" in self.user else "Invitado"
        self.lbl_user = ctk.CTkLabel(self.sidebar, text=f"Usuario: {user_text}")
        self.lbl_user.pack(pady=(0, 10))

        # Botones principales
        self.btn_start = ctk.CTkButton(self.sidebar, text="Iniciar captura", command=self._on_start_capture)
        self.btn_start.pack(fill="x", pady=(6, 4))

        self.btn_stop = ctk.CTkButton(self.sidebar, text="Detener captura", command=self._on_stop_capture, state="disabled")
        self.btn_stop.pack(fill="x", pady=(0, 6))

        # Selector de juego (placeholder, se puede integrar con GameFactory)
        self.game_var = ctk.StringVar(value="AH")
        self.opt_game = ctk.CTkOptionMenu(self.sidebar, values=["AH", "LADRILLOS", "LC"], variable=self.game_var)
        self.opt_game.pack(fill="x", pady=(8, 6))

        # Botón para abrir perfil / historial (placeholder)
        self.btn_profile = ctk.CTkButton(self.sidebar, text="Perfil / Historial", command=self._on_profile)
        self.btn_profile.pack(fill="x", pady=(8, 6))

        # Ajustes (placeholder)
        self.btn_settings = ctk.CTkButton(self.sidebar, text="Ajustes", command=self._on_settings)
        self.btn_settings.pack(fill="x", pady=(8, 6))

        # Espacio inferior para status
        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Estado: Detenido", anchor="w")
        self.lbl_status.pack(side="bottom", fill="x", padx=6, pady=8)

        # Panel principal
        self.main_panel = ctk.CTkFrame(self)
        self.main_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Visor (Canvas / Label con imagen)
        self.visor_frame = ctk.CTkFrame(self.main_panel)
        self.visor_frame.pack(pady=(8, 8))

        self.lbl_visor = ctk.CTkLabel(self.visor_frame, text="Visor de cámara", width=VISOR_WIDTH, height=VISOR_HEIGHT)
        # inicialmente colocamos imagen vacía
        self.lbl_visor.pack()

        # Zona de info/detección
        self.info_frame = ctk.CTkFrame(self.main_panel)
        self.info_frame.pack(fill="x", pady=(8, 0))

        self.lbl_detection = ctk.CTkLabel(self.info_frame, text="Última detección: —", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_detection.pack(anchor="w", padx=6, pady=6)

        # Botón salir
        self.btn_quit = ctk.CTkButton(self.main_panel, text="Salir", command=self._on_close)
        self.btn_quit.pack(anchor="e", padx=6, pady=(12,0))

    # -----------------------
    # EventBus callbacks (SOLO ENCOLAN)
    # -----------------------
    def _enqueue_frame_from_eventbus(self, frame):
        """Callback suscrito a 'frame' que encola el frame para que la UI lo procese."""
        try:
            # Encolamos el frame original (BGR)
            if not self._ui_frame_queue.full():
                self._ui_frame_queue.put(frame)
        except Exception:
            # proteger contra errores de hilos externos
            pass

    def _enqueue_detection_from_eventbus(self, token):
        """Callback suscrito a 'detection' que encola el token para mostrar en la UI."""
        try:
            if not self._detection_queue.full():
                self._detection_queue.put((token, time.time()))
        except Exception:
            pass

    # -----------------------
    # Lógica de control (start/stop)
    # -----------------------
    def _on_start_capture(self):
        """Inicia threads de captura y procesamiento si no existen."""
        if self._running:
            return
        self.lbl_status.configure(text="Estado: Iniciando...")
        # Crear threads si no fueron provistos
        if self.capture_thread is None:
            self.capture_thread = CaptureThread(self.frame_queue,
                                                camera_index=config.CAMERA_INDEX,
                                                width=config.FRAME_WIDTH,
                                                height=config.FRAME_HEIGHT,
                                                target_fps=config.TARGET_FPS)
        # si processing_thread no fue dado, crear con detector por defecto
        if self.processing_thread is None:
            # se asume que ProcessingThread toma frame_queue y event_bus
            self.processing_thread = ProcessingThread(self.frame_queue, self.event_bus)

        # arrancar threads
        self.capture_thread.start()
        self.processing_thread.start()
        self._running = True
        self.lbl_status.configure(text="Estado: Ejecutando")
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")

    def _on_stop_capture(self):
        if not self._running:
            return
        self.lbl_status.configure(text="Estado: Deteniendo...")
        try:
            if self.capture_thread:
                self.capture_thread.stop()
            if self.processing_thread:
                self.processing_thread.stop()
        except Exception:
            pass
        self._running = False
        self.lbl_status.configure(text="Estado: Detenido")
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def _on_profile(self):
        # Placeholder: abrir frame perfil / historial
        ctk.CTkMessagebox(title="Perfil", message="Funcionalidad de perfil pendiente de implementar.") if hasattr(ctk, "CTkMessagebox") else print("[UI] Perfil pulsado")

    def _on_settings(self):
        # Placeholder: abrir ajustes
        ctk.CTkMessagebox(title="Ajustes", message="Ajustes pendientes.") if hasattr(ctk, "CTkMessagebox") else print("[UI] Ajustes pulsado")

    # -----------------------
    # Update loop UI
    # -----------------------
    def _schedule_ui_update(self):
        """Programa la actualización periódica del visor y detecciones."""
        try:
            self._update_from_queues()
        finally:
            # volver a llamar en 30 ms (~33 FPS UI)
            self.after(30, self._schedule_ui_update)

    def _update_from_queues(self):
        """Consume queues y actualiza widgets (ejecuta en hilo principal)."""
        # actualizar frame si hay
        try:
            frame = self._ui_frame_queue.get_nowait()
            self._show_frame_in_label(frame)
        except Empty:
            pass

        # actualizar detección si hay (muestra la más reciente)
        try:
            token, ts = self._detection_queue.get_nowait()
            self._last_detection_ts = ts
            self.lbl_detection.configure(text=f"Última detección: {token}")
        except Empty:
            # si no hay nuevas detecciones, quizá borrar el texto pasado X segundos
            if self._last_detection_ts and (time.time() - self._last_detection_ts) > self._detection_display_seconds:
                self.lbl_detection.configure(text="Última detección: —")
                self._last_detection_ts = 0

    def _show_frame_in_label(self, frame_bgr):
        """Convierte frame BGR -> ImageTk y lo muestra en el label."""
        try:
            # Convertir BGR (OpenCV) a RGB (PIL)
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            # opcional: redimensionar para que quepa en el visor (mantener ratio)
            img = Image.fromarray(frame_rgb)
            img = img.resize((VISOR_WIDTH, VISOR_HEIGHT))
            self._photo_image = ImageTk.PhotoImage(img)
            # Nota: guardamos referencia en self._photo_image para evitar garbage collection
            self.lbl_visor.configure(image=self._photo_image, text="")
        except Exception as e:
            # en caso de error no rompemos la interfaz
            print(f"[UI] Error mostrando frame: {e}")

    # -----------------------
    # Cierre y limpieza
    # -----------------------
    def _on_close(self):
        """Handler de cierre de ventana: detener threads y destruir ventana."""
        # prevenir múltiples llamadas
        if getattr(self, "_closing", False):
            return
        self._closing = True

        # publicar quit por EventBus (otros listeners pueden reaccionar)
        try:
            self.event_bus.publish("quit", None)
        except Exception:
            pass

        # detener hilos locales si existen
        try:
            if self.capture_thread:
                self.capture_thread.stop()
        except Exception:
            pass
        try:
            if self.processing_thread:
                self.processing_thread.stop()
        except Exception:
            pass

        # esperar brevemente para que los hilos terminen
        time.sleep(0.2)

        # cerrar DB si es singleton local
        try:
            if self.db:
                self.db.close()
        except Exception:
            pass

        # destruir ventana
        try:
            self.destroy()
        except Exception:
            pass

# Módulo utilitario: ejecutar la ventana directamente (para pruebas)
def run_gui_for_test(user=None):
    """
    Función de prueba que crea EventBus, colas y lanza la UI.
    Útil para desarrollo: python -m signperu.gui.main_window
    """
    from queue import Queue
    eb = EventBus()
    fq = Queue(maxsize=4)
    # Los threads serán creados por la UI cuando pulses 'Iniciar captura'
    app = MainWindow(event_bus=eb, frame_queue=fq, db=DBManager(), user=user or {"username": "test_user"})
    app.mainloop()

if __name__ == "__main__":
    # Ejecutar prueba rápida
    run_gui_for_test()
