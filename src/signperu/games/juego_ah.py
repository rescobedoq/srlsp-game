#srlsp-game/src/signperu/games/juego_AH.py
# Juego del ahorcado: cuando detecta la letra esperada cuenta éxito
# - Subclase de Game
# - Carga palabras desde archivo "PALABRAS" (mismo directorio) o usa lista por defecto
# - Thread-safe: protege estados con Lock (on_detection será llamado desde un hilo distinto)
# - No modifica UI directamente: publica eventos en EventBus ("game_update", "game_over")
# - Persiste score en DB (si se proporciona DB en app_context)
import threading
import customtkinter as ct
import tkinter as tk
import cv2
from PIL import Image
from signperu.games.game_base import GameBase
from signperu.core.events import EventBus
from signperu.core.capture import CaptureThread
from signperu.core.processing import ProcessingThread
from signperu.core.detector import DetectorWrapper
from signperu.games.clase_ah import ClaseAh  # ruta de la clase juego  ahorcado

class JuegoAH(GameBase):
    def __init__(self, event_bus, db=None, config=None, user=None):
        super().__init__(event_bus, db, config, user)
        # lógica del ahorcado
        self.ObjetoJuego = ClaseAh()
        # UI state
        self.app = None
        self.video_label = None
        self._ctk_image = None
        self.EntradaTexto = None
        self.Texto1 = None
        self.Texto2 = None
        self.Lienzo = None
        self.camara_activa = False
        # Podemos usar detector/capture locales — pero por el app general los hilos
        # se crean en app.py y publican eventos; aquí solo nos subscribimos:
        self.event_bus.subscribe("hand_detected", self._on_hand_detected_event)
        self.event_bus.subscribe("frame_captured", self._on_frame_event)

    def start(self):
        # crear ventana
        self.app = ct.CTk()
        self.app.geometry("1200x690")
        self.app.title("Juego del Ahorcado")
        self.app.resizable(False, False)

        self.Texto1 = tk.StringVar()
        self.Texto2 = tk.StringVar()
        self.Texto2.set("Tus jugadas: ")

        # construir UI (se han extraído partes para brevedad)
        self._build_ui(self.app)
        self.JuegoNuevo()
        self.camara_activa = True
        # arrancar loop
        self.app.protocol("WM_DELETE_WINDOW", self._on_close)
        self.app.mainloop()

    def stop(self):
        # detener: desuscribir eventos y cerrar ventana si existe
        self.camara_activa = False
        try:
            self.event_bus.unsubscribe("hand_detected", self._on_hand_detected_event)
            self.event_bus.unsubscribe("frame_captured", self._on_frame_event)
        except Exception:
            pass
        try:
            if self.app:
                self.app.destroy()
        except Exception:
            pass

    # Public callback para event_bus -> lo convertimos a llamada en hilo principal usar after
    def _on_hand_detected_event(self, letra, frame=None):
        # este callback puede venir desde cualquier hilo, actualizamos UI con .after
        if letra:
            def update():
                try:
                    # mostramos la letra detectada
                    if self.EntradaTexto:
                        self.EntradaTexto.configure(text=letra)
                except Exception:
                    pass
            if self.app:
                self.app.after(0, update)

    # --- Implementación requerida por GameBase (abstract method) ---
    def on_hand_detected(self, letra, frame=None):
        """
        Implementación de la interfaz GameBase.
        Será llamada por quien necesite notificar detecciones de mano.
        Reutiliza la lógica de _on_hand_detected_event para actualizar la UI.
        """
        # Reusamos el mismo flujo: llamar al handler que actualiza UI con .after
        self._on_hand_detected_event(letra, frame=frame)

    def _on_frame_event(self, frame):
        """Actualizamos el feed de la cámara en la UI (frame puede venir anotado)."""
        if frame is None:
            return
        def actualizar_imagen():
            try:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                img = cv2.flip(img, 1)
                pil = Image.fromarray(img)
                if not self._ctk_image:
                    self._ctk_image = ct.CTkImage(dark_image=pil, size=(500, 370))
                    self.video_label.configure(image=self._ctk_image)
                else:
                    self._ctk_image.configure(dark_image=pil)
                    self.video_label.configure(image=self._ctk_image)
            except Exception:
                pass
        if self.app and self.camara_activa:
            self.app.after(0, actualizar_imagen)

    # Métodos del juego (adaptados)
    def JuegoNuevo(self):
        self.ObjetoJuego.nuevojuego()
        self.EstamosJugando = True
        self.__ActualizarVista()

    def BotonEnviar(self):
        if getattr(self, "EstamosJugando", True):
            letra = self.EntradaTexto.cget("text")
            if letra:
                self.ObjetoJuego.jugar(letra.upper())
                if self.ObjetoJuego.getVictoria() or not self.ObjetoJuego.getJugadorEstaVivo():
                    self.EstamosJugando = False
                self.__ActualizarVista()
        else:
            self.JuegoNuevo()
        self.EntradaTexto.configure(text="")

    def __ActualizarVista(self):
        if getattr(self, "EstamosJugando", False):
            letrero = ""
            for x in self.ObjetoJuego.getLetrero():
                letrero += x + " "
            self.Texto1.set(letrero)
            mensaje = "Tus jugadas: "
            for x in self.ObjetoJuego.getLetrasUsadas():
                mensaje += x
            self.Texto2.set(mensaje)
        else:
            if self.ObjetoJuego.getVictoria():
                self.Texto1.set("¡Felicidades! Ganaste.")
            else:
                self.Texto1.set(f"Lo siento, perdiste. La palabra era: {self.ObjetoJuego.getPalabra()}")
            self.Texto2.set("")
        self.__Dibujo()

    # UI builder: reorganiza tu código original (solo partes esenciales)
    def _build_ui(self, app):
        self.entrada_teclado(app)
        self.titulo(app)
        self._build_camera_ui(app)
        self._build_munieco(app)
        self._build_palabra(app)
        self._build_botones(app)

    def entrada_teclado(self, app):
        app.bind("<Return>", lambda x: self.BotonEnviar())
        app.bind("<Control_R>", lambda x: self.JuegoNuevo())
        app.bind("<Control_L>", lambda x: self.JuegoNuevo())
        app.bind("<Escape>", lambda x: self._on_close())
        app.bind("<Key>", self.update_text)

    def update_text(self, event):
        key_pressed = event.char
        if key_pressed not in {'\r', '\x1b', '\uf702', '\uf703'}:
            self.EntradaTexto.configure(text=key_pressed)
    
    def titulo(self, app):
        #Construye el título superior del juego (misma apariencia que en la versión original).
        font_title = ct.CTkFont(family='Consolas', weight='bold', size=25)
        title = ct.CTkLabel(app,
                            text='JUEGO DEL AHORCADO CON SEÑAS',
                            fg_color='steelblue',
                            text_color='white',
                            height=30,
                            font=font_title,
                            corner_radius=8)
        # Usamos grid para colocarlo como antes
        title.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(5, 4), padx=(7, 10))

    def _build_camera_ui(self, app):
        frame_camara = ct.CTkFrame(master=app)
        frame_camara.grid(row=1, column=0, columnspan=2, padx=(14,5), pady=(3,0))
        video_frame = ct.CTkFrame(master=app, corner_radius=12)
        video_frame.grid(row=1, column=0, columnspan=2, padx=(10, 10), pady=(5, 5))
        self.video_label = ct.CTkLabel(master=video_frame, text='', width=600, height=370, corner_radius=12)
        self.video_label.pack(fill=ct.BOTH, padx=(0, 0), pady=(0, 0))
        # Botón start que solo activa la variable camara_activa (el feed ya se publica desde capture)
        btn = ct.CTkButton(master=frame_camara, text='START', width=150, height=40,
                           command=lambda: setattr(self, "camara_activa", True))
        btn.pack(side=ct.LEFT, pady=(5, 10))

    def _build_munieco(self, app):
        self.frame_munieco = ct.CTkFrame(master=app, width=600, height=210, fg_color="transparent")
        self.frame_munieco.grid(row=2, column=0, padx=(12,5), pady=(5,3))
        self.Lienzo = ct.CTkCanvas(self.frame_munieco, width=200, height=200, bg="dark green")
        self.Lienzo.pack(side=ct.LEFT, padx=(15, 20), pady=5)
        self.EntradaTexto = ct.CTkLabel(self.frame_munieco, width=220, height=200, justify=ct.CENTER)
        self.EntradaTexto.pack(side=ct.RIGHT, padx=(20, 5), pady=5)
        myfont = ct.CTkFont(family='Consolas', weight='bold', size=140)
        self.EntradaTexto.configure(fg_color="black", font=myfont, text='')

    def _build_palabra(self, app):
        self.frame_palabra = ct.CTkFrame(master=app, width=750, height=210, fg_color="transparent")
        self.frame_palabra.grid(row=2, column=1, padx=(20,10), pady=(10,10))
        self.Texto1 = tk.StringVar()
        self.Etiqueta1 = ct.CTkLabel(self.frame_palabra, textvariable=self.Texto1, width=680, height=2)
        self.Etiqueta1.pack(side=ct.TOP, padx=(10,5), pady=(5,15))
        self.Etiqueta1.configure(fg_color="transparent", font=("Verdana",60))
        self.Texto2 = tk.StringVar()
        self.Texto2.set("Tus jugadas: ")
        self.Etiqueta2 = ct.CTkLabel(self.frame_palabra, textvariable=self.Texto2, width=40, height=2)
        self.Etiqueta2.pack(side=ct.BOTTOM, padx=(12,5), pady=(15,5))
        self.Etiqueta2.configure(fg_color="transparent", font=("Verdana",30))

    def _build_botones(self, app):
        self.frame_botones = ct.CTkFrame(master=app, height=50, fg_color="transparent")
        self.frame_botones.grid(row=3, column=0, columnspan=2, pady=(4,4), padx=(10,10))
        font_title = ct.CTkFont(family='Consolas', weight='bold', size=24)
        self.BotonEnviarTexto = ct.CTkButton(self.frame_botones, text=">>>", width=80, command=self.BotonEnviar)
        self.BotonEnviarTexto.grid(row=0, column=0, sticky="ew", padx=25)
        self.BotonEnviarTexto.configure(font=font_title, fg_color='steelblue', text_color='white', corner_radius=8)
        self.BotonNuevoJuego = ct.CTkButton(self.frame_botones, text="NUEVO JUEGO", width=250, command=self.JuegoNuevo)
        self.BotonNuevoJuego.grid(row=0, column=1, sticky="ew", padx=120)
        self.BotonNuevoJuego.configure(font=font_title, fg_color='steelblue', text_color='white', corner_radius=8)
        self.BotonSalir = ct.CTkButton(self.frame_botones, text="SALIR", width=120, command=self._on_close)
        self.BotonSalir.grid(row=0, column=2, sticky="ew", padx=25)
        self.BotonSalir.configure(font=font_title, fg_color='steelblue', text_color='white', corner_radius=8)

    def __Dibujo(self):
        # Copié tu lógica de dibujo del ahorcado (idéntica)
        if getattr(self, "EstamosJugando", True):
            oportunidades = self.ObjetoJuego.getOportunidades()
            self.Lienzo.delete("all")
            # dibujado simplificado: muestra etapas como en tu original
            if oportunidades <= 5:
                self.Lienzo.create_line(30,185, 30,20, 100,20, 100,45 ,width=5,fill="white")
                self.Lienzo.create_line(15,193, 15,185, 185,185, 185,193,width=5,fill="white")
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")
            if oportunidades <= 4:
                self.Lienzo.create_line(100,75, 100,135, width=3,fill="white")
            if oportunidades <= 3:
                self.Lienzo.create_line(100,82, 70,112, width=3,fill="white")
            if oportunidades <= 2:
                self.Lienzo.create_line(100,82, 130,112, width=3,fill="white")
            if oportunidades <= 1:
                self.Lienzo.create_line(100,135, 70,165, width=3,fill="white")
        else:
            # victoria/derrota final
            self.Lienzo.delete("all")
            if self.ObjetoJuego.getVictoria():
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")
                self.Lienzo.create_line(100,75, 100,135, width=3,fill="white")
                self.Lienzo.create_line(100,87, 70,57, width=3,fill="white")
                self.Lienzo.create_line(100,87, 130,57, width=3,fill="white")
                self.Lienzo.create_line(100,135, 70,165, width=3,fill="white")
                self.Lienzo.create_line(100,135, 130,165, width=3,fill="white")
            else:
                # muestra muñeco completo (derrota)
                self.Lienzo.create_line(30,185, 30,20, 100,20, 100,45 ,width=5,fill="white")
                self.Lienzo.create_line(15,193, 15,185, 185,185, 185,193,width=5,fill="white")
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")
                self.Lienzo.create_line(100,75, 100,135, width=3,fill="white")
                self.Lienzo.create_line(100,82, 70,112, width=3,fill="white")
                self.Lienzo.create_line(100,82, 130,112, width=3,fill="white")
                self.Lienzo.create_line(100,135, 70,165, width=3,fill="white")
                self.Lienzo.create_line(100,135, 130,165, width=3,fill="white")

    def _on_close(self):
        self.stop()
        try:
            # además detiene la app principal si existe
            if self.app:
                self.app.quit()
        except Exception:
            pass

