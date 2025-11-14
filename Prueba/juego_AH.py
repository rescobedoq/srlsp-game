from ClaseJuego import ClaseJuego
from abecedario import ClasificadorSenia  # Importamos ClasificadorSenia
import threading
import time
import customtkinter as ct
import tkinter as tk
import cv2
from PIL import Image


class Juego_senias:
    def __init__(self, callback):
        # Inicialización de la clase base y otras variables
        self.callback = callback
        self.ObjetoJuego = ClaseJuego()  # Lógica del juego del ahorcado
        self.clasificador_senia = ClasificadorSenia()  # Inicializamos ClasificadorSenia
        self.EstamosJugando = False
        # Variables para la interfaz y la cámara
        self.cap = cv2.VideoCapture(0)
        self.frame_camara, self.video_frame, self.video_label = None, None, None
        # Variables para el juego
        self.EntradaTexto = None
        self.Texto1, self.Texto2 = None, None  # Inicializadas más tarde
        # estado de hilo de la camara
        self.camara_activa = False
        # Imagen
        self.frame_imagen = None
        # Muñeco
        self.frame_munieco, self.Lienzo, self.EntradaTexto = None, None, None
        # Palabra
        self.frame_palabra, self.Texto1, self.Etiqueta1 = None, None, None
        # Jugadas
        self.Texto2, self.Etiqueta2 = None, None
        # Botones
        self.frame_botones, self.BotonEnviarTexto, self.BotonSalir, self.BotonNuevoJuego = None, None, None, None
        # Salir a las opciones
        self.callback = callback

    def ejecutar(self):
        # Configuración de la interfaz
        app = ct.CTk()
        app.geometry("1200x690")
        app.title("Juego del Ahorcado")
        app.resizable(False, False)

        #Crear variables después de inicializar la raíz
        self.Texto1 = tk.StringVar()
        self.Texto2 = tk.StringVar()
        self.Texto2.set("Tus jugadas: ")

        # Crear elementos de la interfaz
        self.entrada_teclado(app)
        self.titulo(app)
        self.camara(app)
        self.munieco(app)
        self.palabra(app)
        self.botones(app)
        self.JuegoNuevo()
        self.camara_activa = True  # Activar la cámara
        
        # Iniciar cámara para detección de manos
        self.iniciar_hilo_camara()

        app.mainloop()

    def iniciar_hilo_camara(self):
        # Inicia un hilo para capturar las letras detectadas por la cámara
        threading.Thread(target=self.procesar_camara, daemon=True).start()

    # Todo LO RELACIONADO CON LA ENTRADA DEL TECLADO  
    def entrada_teclado(self,app):
            app.bind("<Return>",lambda x: self.BotonEnviar())
            app.bind("<Control_R>",lambda x: self.JuegoNuevo())
            app.bind("<Control_L>",lambda x: self.JuegoNuevo())
            app.bind("<Escape>",lambda x: exit())
            # Asociar la función update_text con el evento de presionar tecla
            app.bind("<Key>", self.update_text)

    def update_text(self, event):
        # Obtener la tecla presionada
        key_pressed = event.char

        # Omitir ciertas teclas
        if key_pressed not in {'\r', '\x1b', '\uf702', '\uf703'}:  # '\r': Enter, '\x1b': Escape, '\uf702' y '\uf703': Control
            # Actualizar el texto de la etiqueta
            self.EntradaTexto.configure(text=key_pressed)
    # falta condigurar arreglzr parque no envie la letra aoutomaticamente y este ala izquierda arriba pantalla.
    def procesar_camara(self):
        while self.camara_activa:
            ret, frame = self.cap.read()
            if not ret:
                continue

            letra_detectada, frame_procesado = self.clasificador_senia.procesar_mano(frame)

            if letra_detectada:
                self.EntradaTexto.configure(text=letra_detectada)
                #self.BotonEnviar()  # Enviar automáticamente la letra detectada al juego

            # Actualizar el feed de la cámara en la interfaz
            frame_procesado = cv2.cvtColor(frame_procesado, cv2.COLOR_BGR2RGBA)
            frame_procesado = cv2.flip(frame_procesado, 1)
            img = Image.fromarray(frame_procesado)

            # Actualizar la interfaz gráfica usando el hilo principal de Tkinter
            # solucionamos problemas ValueError: list.remove(x): x not in list
            def actualizar_imagen():
                # Reutilizamos la misma instancia de CTkImage
                if not hasattr(self, "_ctk_image"):
                    self._ctk_image = ct.CTkImage(dark_image=img, size=(500, 370))
                else:
                    self._ctk_image.configure(dark_image=img)
                self.video_label.configure(image=self._ctk_image)

            if self.camara_activa:
                self.video_label.after(0, actualizar_imagen)
    # IMPLEMENTACION RELACIONADO CON EL JUEGO DEL AHORCADO 

    # Para dibujar al muñeco del ahorcado 

    # Cierre desvinculacion 
    def cerrar_ventana(self, app):
        self.camara_activa = False  # Detener el hilo de la cámara
        if self.cap.isOpened():
            self.cap.release()  # Liberar la cámara

        self.desvincular_eventos(app)
        app.destroy()
        if self.callback:
           self.callback()
    
    def desvincular_eventos(self, app):
        app.unbind("<Return>")
        app.unbind("<Control_R>")
        app.unbind("<Control_L>")
        app.unbind("<Escape>")
        app.unbind("<Key>")

if __name__ == "__main__":

    juego = Juego_senias(callback=None)
    juego.ejecutar()