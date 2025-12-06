import tkinter as tk
from tkinter import ttk
import random
from PIL import Image, ImageTk
import imageio
import threading
import cv2
import pygame 
from tkinter import Toplevel
from abecedario import ClasificadorSenia  # Importamos ClasificadorSenia



class Arkanoid:
    def __init__(self, callback):
        pygame.init()
        self.callback = callback
        self.ventana = tk.Tk()
        self.ventana.title("Arkanoid")
        self.ancho = 800
        self.alto = 600
        self.ventana.geometry(f"{self.ancho}x{self.alto}")
        self.ventana.resizable(False, False)
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.imageFondosGame=['./juego_ladrillosMEDIA/wood.png','./juego_ladrillosMEDIA/planets.png','./juego_ladrillosMEDIA/sea.jpeg']
        self.video_running = False
        self.estilo_botones()
        #cv2
        self.clasificador_senia = ClasificadorSenia()
        self.camara = cv2.VideoCapture(0)

        # Establecer resolución de la cámara
        self.camara.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.en_juego =False
        if not self.camara.isOpened():
            print("Error: No se pudo acceder a la cámara")
            self.camara_activa =False
            return
        else:
            self.camara_activa =True
            
        self.menu_principal()

    def estilo_botones(self):
        # Crear un estilo para los botones
        style = ttk.Style()
        style.configure("Custom.TButton",
                        background="#00BFFF",  # Celeste
                        foreground="black",  # Texto blanco
                        font=("Arial", 12, "bold"),
                        padding=2,
                        borderwidth=0)
        style.map("Custom.TButton",
                  background=[("active", "#009ACD")]) 
    def sonidoBoton(self):
        pygame.mixer.music.load('./juego_ladrillosMEDIA/botonSonido.mp3')
        pygame.mixer.music.play()
    def menu_principal(self):
        
        self.limpiar_ventana()
        self.canvas = tk.Canvas(self.ventana, width=self.ancho, height=self.alto, bg="black")
        self.canvas.pack()
        
        self.iniciarFrameVideo()
        
        if not self.video_running:
            self.reproducir_video()
        
        # Cargar y redimensionar la imagen PNG
        original_image = Image.open("./juego_ladrillosMEDIA/arkanoid.png")  # Especifica la ruta de tu imagen
        new_width = 400  # Ajusta este valor al ancho deseado
        aspect_ratio = original_image.height / original_image.width
        new_height = int(new_width * aspect_ratio)
        resized_image = original_image.resize((new_width, new_height), Image.ANTIALIAS)
        self.imagen_logo = ImageTk.PhotoImage(resized_image)

        # Crear un Label para contener la imagen redimensionada
        label_logo = tk.Label(self.ventana, image=self.imagen_logo, bg="black")
        # Dibujar el Label en el canvas usando create_window
        self.canvas.create_window(self.ancho / 2, self.alto / 2 - 150, window=label_logo)
        
        
        boton_empezar = ttk.Button(self.ventana, text="Empezar Juego", style="Custom.TButton", command=lambda: (self.sonidoBoton(),self.seleccionar_nivel()))
        self.canvas.create_window(self.ancho / 2, self.alto / 2 - 50, window=boton_empezar)

        boton_como_jugar = ttk.Button(self.ventana, text="Cómo Jugar", style="Custom.TButton",command=lambda: (self.sonidoBoton(),self.como_jugar()))
        self.canvas.create_window(self.ancho / 2, self.alto / 2, window=boton_como_jugar)

        boton_salir = ttk.Button(self.ventana, text="Salir",style="Custom.TButton", command=lambda: (self.sonidoBoton(),self.cerrar()))
        self.canvas.create_window(self.ancho / 2, self.alto / 2 + 50, window=boton_salir)
        
    def iniciarFrameVideo(self):
        # Crear un frame que será la ventana para mostrar el video
        self.video_frame = tk.Frame(self.canvas, width=self.ancho, height=self.alto)
        self.video_frame.pack_propagate(False)  # Evitar que el frame cambie de tamaño
        self.canvas.create_window(0, 0, anchor=tk.NW, window=self.video_frame)

        # Label para mostrar los frames
        self.label_video = tk.Label(self.video_frame)
        self.label_video.pack()
        
    def cerrar(self):
        # Detener la música
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        
        # Detener el video
        self.video_running = False

        # Cerrar la ventana
        self.ventana.destroy()
        if self.camara.isOpened():
            self.camara.release()
        if self.callback:
           self.callback()
    def reproducir_video(self):
        self.video_running = True
        video = imageio.get_reader('./juego_ladrillosMEDIA/stars.mp4', 'ffmpeg')

        def loop_video():
            for frame in video:
                if not self.video_running:
                    break

                # Redimensionar el frame al tamaño del canvas
                frame_image = Image.fromarray(frame)
                frame_image = frame_image.resize((self.ancho, self.alto), Image.ANTIALIAS)
                frame_tk = ImageTk.PhotoImage(frame_image)
                
                if self.label_video.winfo_exists():
                    # Actualizar el Label dentro de la ventana
                    self.label_video.config(image=frame_tk)
                    self.label_video.image = frame_tk

                    self.label_video.update()
                    self.label_video.after(33)  # Aproximadamente 30 fps

            video.close()

        threading.Thread(target=loop_video, daemon=True).start()
    def detener_video(self):
        self.video_running = False
        
            
    def como_jugar(self):
        self.detener_video()
        self.limpiar_ventana()
        self.canvas = tk.Canvas(self.ventana, width=self.ancho, height=self.alto, bg="black")
        self.canvas.pack()

        # Cargar y mostrar la imagen
        imagen = Image.open("./juego_ladrillosMEDIA/JUGAR.png")  # Cambia la ruta a tu archivo de imagen
        imagen = imagen.resize((self.ancho, self.alto), Image.ANTIALIAS)  # Ajusta el tamaño de la imagen
        self.imagen_tk = ImageTk.PhotoImage(imagen)  # Referencia necesaria para evitar recolección de basura
        self.canvas.create_image(0, 0, image=self.imagen_tk, anchor=tk.NW)

        # Crear un Frame para contener el botón
        frame_boton = tk.Frame(self.ventana, bg="black")

        # Botón "Volver"
        boton_volver = ttk.Button(frame_boton, text="Volver",style="Custom.TButton", command=lambda: (self.sonidoBoton(),self.menu_principal()))
        boton_volver.pack()

        # Añadir el Frame al canvas
        self.canvas.create_window(self.ancho / 2, self.alto / 2 + 50, window=frame_boton, anchor=tk.CENTER)

    def seleccionar_nivel(self):
        self.detener_video()
        self.limpiar_ventana()
        self.canvas = tk.Canvas(self.ventana, width=self.ancho, height=self.alto, bg="black")
        self.canvas.pack()

        self.canvas.create_text(self.ancho / 2, self.alto / 2 - 100, text="Selecciona un nivel", fill="white", font=("Arial", 24))

        imagen_nivel_1 = Image.open("./juego_ladrillosMEDIA/nivel1.png").resize((150, 150), Image.ANTIALIAS)
        imagen_nivel_1 = ImageTk.PhotoImage(imagen_nivel_1)  # Asegúrate de tener la imagen en el directorio
        
        imagen_nivel_2 = Image.open("./juego_ladrillosMEDIA/nivel2.png").resize((150, 150), Image.ANTIALIAS)
        imagen_nivel_2 = ImageTk.PhotoImage(imagen_nivel_2)

        imagen_nivel_3 = Image.open("./juego_ladrillosMEDIA/nivel3.png").resize((150, 150), Image.ANTIALIAS)
        imagen_nivel_3 = ImageTk.PhotoImage(imagen_nivel_3)
        
        
        boton_nivel_1 = tk.Button(self.ventana, image=imagen_nivel_1, command=lambda: (self.sonidoBoton(), self.empezar_juego(1)))
        boton_nivel_1.image = imagen_nivel_1  # Mantener referencia para evitar garbage collection
        self.canvas.create_window(self.ancho / 2 - 200, self.alto / 2, window=boton_nivel_1)

        boton_nivel_2 = tk.Button(self.ventana, image=imagen_nivel_2, command=lambda: (self.sonidoBoton(), self.empezar_juego(2)))
        boton_nivel_2.image = imagen_nivel_2
        self.canvas.create_window(self.ancho / 2, self.alto / 2, window=boton_nivel_2)

        boton_nivel_3 = tk.Button(self.ventana, image=imagen_nivel_3, command=lambda: (self.sonidoBoton(), self.empezar_juego(3)))
        boton_nivel_3.image = imagen_nivel_3
        self.canvas.create_window(self.ancho / 2 + 200, self.alto / 2, window=boton_nivel_3)

    def empezar_juego(self, nivel):
        self.limpiar_ventana()
        
        self.canvas = tk.Canvas(self.ventana, width=self.ancho, height=self.alto, bg="black")
        self.canvas.pack()
        
        
        fondo = Image.open(self.imageFondosGame[nivel-1])  # Cambia por la ruta de tu imagen
        fondo = fondo.resize((self.ancho, self.alto), Image.ANTIALIAS)
        self.fondo_imagen = ImageTk.PhotoImage(fondo)
        self.canvas.create_image(0, 0, image=self.fondo_imagen, anchor=tk.NW)
        
        pygame.mixer.music.load("./juego_ladrillosMEDIA/aura.mp3")  # Cambia por la ruta de tu archivo MP3
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)  # Reproducir en bucle infinito
        
        self.paleta = self.canvas.create_rectangle(self.ancho / 2 - 40, self.alto - 20, self.ancho / 2 + 40, self.alto - 10, fill="white")
        self.bola = self.canvas.create_oval(self.ancho / 2 - 10, self.alto / 2 - 10+ 250, self.ancho / 2 + 10, self.alto / 2 + 10+250, fill="red")

        self.bola_dx = random.choice([-6, 6])
        self.bola_dy = -6

        self.bloques = []
        self.crear_bloques(nivel)

        self.en_juego = True
        # Crear una nueva ventana
        
        new_window = Toplevel(self.ventana)
        new_window.title("Video Capture")
        new_window.geometry("500x500")
        
        #poner a la derecha de la ventana principal
        self.ventana.update_idletasks()  # Asegurarse de que la geometría esté actualizada
        root_geometry = self.ventana.geometry()  # Ejemplo: "300x200+100+100"

        parts = root_geometry.split('+')
        size = parts[0].split('x')
        root_width=size[0]
        root_height=size[1]
        root_x=parts[1]
        root_y =parts[2]

        # Calcular posición de la nueva ventana (a la derecha de la ventana principal)
        new_x = int(root_x) + int(root_width) + 10  # Añade un margen de 10 píxeles
        new_y = int(root_y)  # Mantener la misma altura

        # Establecer la posición de la nueva ventana
        new_window.geometry(f"500x500+{new_x}+{new_y}")
    
        # Crear un Label para mostrar el video
        self.video_label = tk.Label(new_window)
        self.video_label.pack()
        
        self.actualizacion = self.ventana.after(20, lambda:self.mover_bola(nivel))
        #self.procesar_camara()
    def procesar_camara(self):
        """Procesa las imágenes de la cámara para detectar la letra señalada."""

        ret, frame = self.camara.read()

        if not ret:
            print("Error: No se pudo leer el frame de la cámara")
            return
        
        # Procesar la mano con tolerancia: el clasificador puede devolver
        # - una letra (str) o None
        # - o una tupla/lista con distintos formatos (letra, info, bbox)
        res = self.clasificador_senia.procesar_mano(frame)
        letra = None
        x1 = y1 = x2 = y2=0

        try:
            if isinstance(res, (tuple, list)):
                    # formato (letra, _, bbox) o (letra, bbox)
                if len(res) == 3:
                    letra, _, bbox = res
                    if isinstance(bbox, (tuple, list)) and len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                elif len(res) == 2:
                    letra, bbox = res
                    if isinstance(bbox, (tuple, list)) and len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                else:
                        # si la estructura es inesperada, tomar primer elemento como letra
                        letra = res[0] if len(res) > 0 else None
            else:
                # res es un str (p. ej. 'A') o None
                letra = res
        except Exception:
            letra = None
            x1 = y1 = x2 = y2 = 0

        # Dibujar sólo si el bbox es válido (evita rectángulos basura)
        if (x1, y1, x2, y2) != (0, 0, 0, 0):
            try:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
            except Exception:
                pass

        if letra is not None:
            try:
                cv2.putText(frame, str(letra), (x1, y1 - 10 if y1-10>0 else y1 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA)
            except Exception:
                pass
        
        # convertir y mostrar en tkinter
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)

        #código que actualiza el widget con la imagen 
        imgtk = ImageTk.PhotoImage(image=img)
        # Mostrar el frame en el Label
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)    
            
        if letra:
            print(f"Letra detectada: {letra}")  # Mensaje cuando se detecta una letra
            if letra == 'A':
                self.mover_paleta_izquierda()
            if letra =='B':
                self.mover_paleta_derecha()

        # Pausar ligeramente el bucle para evitar un ciclo infinito rápido
        pygame.time.delay(10)  # Esto ralentiza el bucle del hilo de la cámara
        
        
    def limpiar_ventana(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()
            
    def generar_letraM(self):
    
        arrayPosicionCuadrados=[]
        
        #costado izquierdo
        for fila in range(0,14):
            for columna in range(1,7):
                arrayPosicionCuadrados.append(fila*23+columna)
        
        #costado derecho
        for fila in range(0,14):
            for columna in range(18,24):
                arrayPosicionCuadrados.append(fila*23+columna)
        #\ de m
        inicialValue1=30
        value1=inicialValue1
        for columna in range(1,6):
            for fila in range(0,6):
                arrayPosicionCuadrados.append(value1)
                value1=value1+23
                
            value1=inicialValue1+24*columna
        #raya mediana
        inicialValue2=127
        for fila in range(0,6):
            arrayPosicionCuadrados.append(inicialValue2)
            inicialValue2=inicialValue2+23
        
        #/ de m
        inicialValue3=40
        value3=inicialValue3
        for columna in range(1,6):
            for fila in range(0,6):
                arrayPosicionCuadrados.append(value3)
                value3=value3+23
                
            value3=inicialValue3+22*columna
        
        
        return arrayPosicionCuadrados
    
    def generar_flecha(self):
    
        arrayPosicionCuadrados=[]
        
        #costado izquierdo
        inicialValue1=140
        value1=inicialValue1
        for fila in range(2,13,2):
            for columna in range(0,fila):
                arrayPosicionCuadrados.append(value1)
                value1=value1+23
            inicialValue1=inicialValue1-22
            value1=inicialValue1
        
        #rectangulo interno
        for fila in range(123,193,23):
            for columna in range(0,9):
                arrayPosicionCuadrados.append(fila+columna)
        
        #costado derecho
        inicialValue2=160
        value2=inicialValue2
        for fila in range(2,13,2):
            for columna in range(0,fila):
                arrayPosicionCuadrados.append(value2)
                value2=value2+23
            inicialValue2=inicialValue2-24
            value2=inicialValue2
            
        return arrayPosicionCuadrados
    def generar_calavera(self):
    
        arrayPosicionCuadrados=[]
        array1 = [i for i in range(8, 16)]
        array2 =[29,30,39,40,52,63,74,97,87,110,212,236,225,247,286,309,289,312,218,241,219,242]
        array3 = [i for i in range(119, 189,23)]
        array4 = [i for i in range(134, 204,23)]
        array5 = [i for i in range(260, 307,23)]
        array6 = [i for i in range(269, 316,23)]
        
        array7 = [i for i in range(121, 168,23)]
        array8 = [i for i in range(99, 192,23)]
        array9 = [i for i in range(100, 193,23)]
        array10 = [i for i in range(101, 194,23)]
        array11 = [i for i in range(125, 172,23)]
        
        array12 = [i for i in range(128, 175,23)]
        array13 = [i for i in range(106, 199,23)]
        array14 = [i for i in range(107, 200,23)]
        array15 = [i for i in range(108, 201,23)]
        array16 = [i for i in range(132, 179,23)]
        array17 = [i for i in range(330, 338)]
        
        arrayPosicionCuadrados = (
            array1 + array2 + array3 + array4 + array5 + array6 +
            array7 + array8 + array9 + array10 + array11 +
            array12 + array13 + array14 + array15 + array16+array17
        )
        return arrayPosicionCuadrados
    def generar_coordenadas(self,nivel):
        x1=20
        y1=50
        x2=45
        y2=70
        coordenadas = []
        columnas = 23
        filas=15

        
        if nivel == 1:
            #primer nivel letra M
            arrayRectangulosAceptados=self.generar_letraM()
        elif nivel ==2:
            #nivel 2 flecha doble
            arrayRectangulosAceptados=self.generar_flecha()
        else:
            #nivel 3 
            arrayRectangulosAceptados=self.generar_calavera()
            
        numeroDeCuadrado=1
        for fila in range(filas):
            for columna in range(columnas):
                x1 = x1+30
                x2 = x2 +30
                if numeroDeCuadrado in arrayRectangulosAceptados:
                    coordenadas.append((x1, y1, x2, y2))

                numeroDeCuadrado=numeroDeCuadrado+1
            y1=y1+25
            y2=y2+25
            
            x1 = 20
            x2 = 45
        return coordenadas
    def crear_bloques(self, nivel):
        colores = ["blue", "red", "green", "yellow", "purple", "orange", "pink"]  # Lista de colores
        
        coordenadasCuadrados=self.generar_coordenadas(nivel)
        for coords in coordenadasCuadrados:
            color_aleatorio = random.choice(colores)  # Escoge un color aleatorio
            bloque = self.canvas.create_rectangle(coords[0], coords[1], coords[2], coords[3], fill=color_aleatorio, outline="white")
            self.bloques.append(bloque)


    def mover_paleta_izquierda(self):
        
        pos_paleta=self.canvas.coords(self.paleta)
        if pos_paleta[0]-20 >= 0:
            self.canvas.move(self.paleta, -20, 0)
        

    def mover_paleta_derecha(self):
        
        pos_paleta=self.canvas.coords(self.paleta)
        if pos_paleta[0]+20 <= 720:
            self.canvas.move(self.paleta, 20, 0)
        

    def mover_bola(self,nivel):
        if not self.en_juego:
            return
        self.procesar_camara()
        
        self.canvas.move(self.bola, self.bola_dx, self.bola_dy)
        pos_bola = self.canvas.coords(self.bola)

        if pos_bola[0] <= 0 or pos_bola[2] >= self.ancho:
            self.bola_dx = -self.bola_dx

        if pos_bola[1] <= 0:
            self.bola_dy = -self.bola_dy

        if pos_bola[3] >= self.alto:
            self.fin_del_juego("Perdiste",nivel)

        pos_paleta = self.canvas.coords(self.paleta)
        if (pos_bola[2] >= pos_paleta[0] and pos_bola[0] <= pos_paleta[2] and
                pos_bola[3] >= pos_paleta[1] and pos_bola[3] <= pos_paleta[3]):
            self.bola_dy = -self.bola_dy

        for bloque in self.bloques[:]:
            pos_bloque = self.canvas.coords(bloque)
            if (pos_bola[2] >= pos_bloque[0] and pos_bola[0] <= pos_bloque[2] and
                    pos_bola[3] >= pos_bloque[1] and pos_bola[1] <= pos_bloque[3]):
                self.canvas.delete(bloque)
                self.bloques.remove(bloque)
                self.bola_dy = -self.bola_dy
                break

        if not self.bloques:
            self.fin_del_juego("Ganaste",nivel)

        self.actualizacion = self.ventana.after(20, lambda:self.mover_bola(nivel))

    def fin_del_juego(self, mensaje,nivel):
        self.en_juego = False
        pygame.mixer.music.stop()
        
        

        # Crear un rectángulo semitransparente para el fondo
        self.canvas.create_rectangle(
            0, 0,  # Coordenadas superiores izquierda
            self.ancho, self.alto,  # Coordenadas inferiores derecha
            fill="black", stipple="gray75", outline=""
        )
        self.canvas.create_text(self.ancho / 2, self.alto / 2, text=mensaje, fill="white", font=("Arial", 24))
        contenedor_botones = tk.Frame(self.ventana)
        contenedor_botones.pack()

        # Crear botones
        boton_reintentar = tk.Button(contenedor_botones, text="Reintentar", command=lambda: (self.sonidoBoton(),self.reiniciar_juego(nivel)))
        boton_reintentar.grid(row=0, column=0, padx=10)
        
        boton_menu = tk.Button(contenedor_botones, text="Menu", command=lambda:  (self.sonidoBoton(),self.menu_principal()))
        boton_menu.grid(row=0, column=1, padx=10)

        # Colocar el contenedor en el canvas
        self.canvas.create_window(self.ancho / 2, self.alto / 2 + 50, window=contenedor_botones)

    def reiniciar_juego(self,nivel):
        self.empezar_juego(nivel)

    def iniciar_juego(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    juego = Arkanoid(callback=None)
    juego.iniciar_juego()
