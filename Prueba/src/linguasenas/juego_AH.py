from linguasenas.games.ClaseJuego import ClaseJuego
from linguasenas.tools.abecedario import ClasificadorSenia
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

    # TODOD LO RELACIONADO CON LA ENTRADA DEL TECLADO  
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
    def JuegoNuevo(self):
        self.EstamosJugando = True
        self.ObjetoJuego.nuevojuego()
        #AÑADIR IMAGEN PARA LA PALABRA
        self.__ActualizarVista()

    def BotonEnviar(self):
        if self.EstamosJugando:
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
        if self.EstamosJugando:
            # Actualizamos la palabra oculta y las letras usadas
            letrero=""
            for x in self.ObjetoJuego.getLetrero(): letrero+=x+" "  
            self.Texto1.set(letrero)
            mensaje="Tus jugadas: "
            for x in self.ObjetoJuego.getLetrasUsadas():mensaje+=x
            self.Texto2.set(mensaje)
            #self.Texto1.set(" ".join(self.ObjetoJuego.getLetrero()))
            #self.Texto2.set("Tus jugadas: " + ", ".join(self.ObjetoJuego.getLetrasUsadas()))
        else:
            # Mensajes finales
            if self.ObjetoJuego.getVictoria():
                self.Texto1.set("¡Felicidades! Ganaste.")
            else:
                self.Texto1.set(f"Lo siento, perdiste. La palabra era: {self.ObjetoJuego.getPalabra()}")
            self.Texto2.set("")
        self.__Dibujo() # esto acciona para dibujar el hombrecito

    def titulo(self, app):
        font_title = ct.CTkFont(family='Consolas', weight='bold', size=25)
        title = ct.CTkLabel(app, text='JUEGO DEL AHORCADO CON SEÑAS', fg_color='steelblue',
                            text_color='white', height=30, font=font_title, corner_radius=8)
        title.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(5, 4), padx=(7, 10))
    #Interfaz de camara
    def camara(self, app):
        self.frame_camara = ct.CTkFrame(master=app)   #, width=680, height = 400
        self.frame_camara.grid(row=1, column=0, columnspan=2, padx = (14,5), pady=(3,0))

        self.video_frame = ct.CTkFrame(master=app, corner_radius=12)
        self.video_frame.grid(row=1, column=0, columnspan=2, padx=(10, 10), pady=(5, 5))

        # Etiqueta para el feed de video
        self.video_label = ct.CTkLabel(master=self.video_frame, text='', width=600, height=370, corner_radius=12)
        self.video_label.pack(fill=ct.BOTH, padx=(0, 0), pady=(0, 0))

        # Cargar imagen de cámara apagada
        camera_off_image = ct.CTkImage(light_image=Image.open("camara_apagada.png"), size=(590, 350))
        self.video_label.configure(image=camera_off_image)

        # Create a button to start the camera feed
        self.Camera_feed_start = ct.CTkButton(master=self.frame_camara, text='START', width=150, height=40, border_width=0, corner_radius=12, command=lambda: self.open_camera1()) #, command=lambda: self.camara_ia.open_camera1()
        self.Camera_feed_start.pack(side=ct.LEFT, pady=(5, 10))

    # Interfaz del ahorcado muñeco
    def munieco(self, app):
        #self.EntradaTexto = ct.CTkLabel(app, text='', fg_color="black", width=200, height=50)
        #self.EntradaTexto.grid(row=2, column=0)
        self.frame_munieco=ct.CTkFrame(master=app, width=600, height=210, fg_color="transparent")
        self.frame_munieco.grid(row=2, column=0, padx = (12,5),pady=(5,3))

        self.Lienzo=ct.CTkCanvas(self.frame_munieco, width=200, height=200, bg="dark green")
        self.Lienzo.pack(side=ct.LEFT, padx=(15, 20), pady=5)

        self.EntradaTexto=ct.CTkLabel(self.frame_munieco, width=220, height=200, justify=ct.CENTER)
        self.EntradaTexto.pack(side=ct.RIGHT, padx=(20, 5), pady=5)
        myfont = ct.CTkFont(
            family='Consolas',
            weight='bold',
            size=140
        )
        self.EntradaTexto.configure(fg_color="black", font=myfont, text='')

    # Modificaciones para palabra como se ve en el recuadro falta ajustar
    def palabra(self, app):

        self.frame_palabra=ct.CTkFrame(master=app, width=750, height=210, fg_color="transparent")
        self.frame_palabra.grid(row=2, column=1, padx = (20,10),pady=(10,10))
        #Palabra
        self.Texto1=tk.StringVar()

        self.Etiqueta1=ct.CTkLabel(self.frame_palabra, textvariable=self.Texto1, width=680, height=2)
        self.Etiqueta1.pack(side=ct.TOP, padx = (10,5), pady=(5,15))
        self.Etiqueta1.configure(fg_color="transparent", font=("Verdana",60))

        #Jugadas
        self.Texto2=tk.StringVar()
        self.Texto2.set("Tus jugadas: ")

        self.Etiqueta2=ct.CTkLabel(self.frame_palabra, textvariable=self.Texto2, width=40, height=2)
        self.Etiqueta2.pack(side=ct.BOTTOM, padx = (12,5), pady=(15,5))
        self.Etiqueta2.configure(fg_color="transparent" ,font=("Verdana",30))

    def botones(self, app):

        self.frame_botones = ct.CTkFrame(master=app, height=50, fg_color="transparent")
        self.frame_botones.grid(row=3, column=0, columnspan=2, pady=(4,4), padx=(10,10))

        font_title = ct.CTkFont(family='Consolas', weight='bold', size=24)

        self.BotonEnviarTexto=ct.CTkButton(self.frame_botones, text=">>>", width=80, command = self.BotonEnviar)
        self.BotonEnviarTexto.grid(row=0, column=0, sticky="ew", padx = 25)
        self.BotonEnviarTexto.configure(font=font_title, fg_color='steelblue', text_color= 'white', corner_radius= 8)  

        self.BotonNuevoJuego = ct.CTkButton(self.frame_botones, text="NUEVO JUEGO", width=250, command=self.JuegoNuevo)
        self.BotonNuevoJuego.grid(row=0, column=1, sticky="ew", padx = 120)
        self.BotonNuevoJuego.configure(font=font_title, fg_color='steelblue', text_color= 'white', corner_radius= 8)

        self.BotonSalir=ct.CTkButton(self.frame_botones, text="SALIR", width=120, command =lambda: self.cerrar_ventana(app))
        self.BotonSalir.grid(row=0, column=2, sticky="ew", padx = 25)
        self.BotonSalir.configure(font=font_title, fg_color='steelblue', text_color= 'white', corner_radius= 8)

    # Para dibujar al muñeco del ahorcado 
    def __Dibujo(self):

        if self.EstamosJugando:
            oportunidades=self.ObjetoJuego.getOportunidades()
            if oportunidades==1:
                self.Lienzo.delete("all")
                self.Lienzo.create_line(30,185, 30,20, 100,20, 100,45 ,width=5,fill="white")#horca
                self.Lienzo.create_line(15,193, 15,185, 185,185, 185,193,width=5,fill="white")#horca
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")#cabeza
                self.Lienzo.create_line(100,75, 100,135, width=3,fill="white")#torso
                self.Lienzo.create_line(100,82, 70,112, width=3,fill="white")#brazo1
                self.Lienzo.create_line(100,82, 130,112, width=3,fill="white")#brazo2
                self.Lienzo.create_line(100,135, 70,165, width=3,fill="white")#pierna1
            elif oportunidades==2:
                self.Lienzo.delete("all")
                self.Lienzo.create_line(30,185, 30,20, 100,20, 100,45 ,width=5,fill="white")#horca
                self.Lienzo.create_line(15,193, 15,185, 185,185, 185,193,width=5,fill="white")#horca
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")#cabeza
                self.Lienzo.create_line(100,75, 100,135, width=3,fill="white")#torso
                self.Lienzo.create_line(100,82, 70,112, width=3,fill="white")#brazo1
                self.Lienzo.create_line(100,82, 130,112, width=3,fill="white")#brazo2
            elif oportunidades==3:
                self.Lienzo.delete("all")
                self.Lienzo.create_line(30,185, 30,20, 100,20, 100,45 ,width=5,fill="white")#horca
                self.Lienzo.create_line(15,193, 15,185, 185,185, 185,193,width=5,fill="white")#horca
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")#cabeza
                self.Lienzo.create_line(100,75, 100,135, width=3,fill="white")#torso
                self.Lienzo.create_line(100,82, 70,112, width=3,fill="white")#brazo1
            elif oportunidades==4:
                self.Lienzo.delete("all")
                self.Lienzo.create_line(30,185, 30,20, 100,20, 100,45 ,width=5,fill="white")#horca
                self.Lienzo.create_line(15,193, 15,185, 185,185, 185,193,width=5,fill="white")#horca
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")#cabeza
                self.Lienzo.create_line(100,75, 100,135, width=3,fill="white")#torso
            elif oportunidades==5:
                self.Lienzo.delete("all")
                self.Lienzo.create_line(30,185, 30,20, 100,20, 100,45 ,width=5,fill="white")#horca
                self.Lienzo.create_line(15,193, 15,185, 185,185, 185,193,width=5,fill="white")#horca
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")#cabeza
            else:
                self.Lienzo.delete("all")
                self.Lienzo.create_line(30,185, 30,20, 100,20, 100,45 ,width=5,fill="white")#horca
                self.Lienzo.create_line(15,193, 15,185, 185,185, 185,193,width=5,fill="white")#horca
        else:
            if self.ObjetoJuego.getVictoria():
                self.Lienzo.delete("all")
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")#cabeza
                self.Lienzo.create_line(100,75, 100,135, width=3,fill="white")#torso
                self.Lienzo.create_line(100,87, 70,57, width=3,fill="white")#brazo1
                self.Lienzo.create_line(100,87, 130,57, width=3,fill="white")#brazo2
                self.Lienzo.create_line(100,135, 70,165, width=3,fill="white")#pierna1
                self.Lienzo.create_line(100,135, 130,165, width=3,fill="white")#pierna2
            else:
                self.Lienzo.delete("all")
                self.Lienzo.create_line(30,185, 30,20, 100,20, 100,45 ,width=5,fill="white")#horca
                self.Lienzo.create_line(15,193, 15,185, 185,185, 185,193,width=5,fill="white")#horca
                self.Lienzo.create_oval(85,45, 115,75, width=3,fill="dark green",outline="white")#cabeza
                self.Lienzo.create_line(100,75, 100,135, width=3,fill="white")#torso
                self.Lienzo.create_line(100,82, 70,112, width=3,fill="white")#brazo1
                self.Lienzo.create_line(100,82, 130,112, width=3,fill="white")#brazo2
                self.Lienzo.create_line(100,135, 70,165, width=3,fill="white")#pierna1
                self.Lienzo.create_line(100,135, 130,165, width=3,fill="white")#pierna2

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