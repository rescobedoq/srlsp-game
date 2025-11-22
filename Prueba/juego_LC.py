import pygame
import random
from abecedario import ClasificadorSenia
import cv2
from threading import Thread
from PIL import Image
import numpy as np

# Configuración de la pantalla
ANCHO = 800
ALTO = 600
COLOR_LETRA = (0, 0, 0)
FPS = 60

class JuegoLetras:
    def __init__(self,callback):
        # Salir a las opciones
        self.callback = callback
        self.pantalla = None
        self.reloj = None
        self.fuente = None
        self.fondo = None
        self.clasificador_senia = None
        self.camara = None

        # Letras que caen
        self.letras = []
        self.velocidad = 2
        self.letra_detectada = None

        # Estado del juego
        self.jugando = True
        self.puntuacion = 0

        # Vidas del jugador (agregamos 50 vidas)
        self.vidas = 20
        self.boton_empezar = None
        self.boton_salir = None

    # Funcion controladora para iniciar juego2
    def inicializar(self):
        """Inicializa todos los componentes necesarios para el juego."""
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Minijuego: Letras que caen")
        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.Font(None, 74)

        # Cargar la imagen de fondo
        self.fondo = pygame.image.load("fondo1.jpg")
        # Asegurarnos de que se ajuste al tamaño de la pantalla
        self.fondo = pygame.transform.scale(self.fondo, (ANCHO, ALTO))

        # Inicializar detección de señas
        self.clasificador_senia = ClasificadorSenia()
        self.camara = cv2.VideoCapture(0)

        # Establecer resolución de la cámara
        self.camara.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.camara.isOpened():
            print("Error: No se pudo acceder a la cámara")
            self.jugando = False
            return

        # Configurar botones
        self.boton_empezar = pygame.Rect(100, 500, 200, 50) # Posición y tamaño del botón "Empezar"
        self.boton_salir = pygame.Rect(500, 500, 200, 50) # Posición y tamaño del botón "Salir"

    def generar_letra(self):
        """Genera una letra aleatoria que comienza en una posición aleatoria."""
        letra = chr(random.randint(65, 90))  # Letras A-Z
        x = random.randint(50, ANCHO - 50)
        y = -50  # Comienza fuera de la pantalla
        self.letras.append({"letra": letra, "posicion": [x, y]})

    def procesar_camara(self):
        """Procesa las imágenes de la cámara para detectar la letra señalada."""
        print("Iniciando captura de cámara...")
        while self.jugando:
            ret, frame = self.camara.read()
            if not ret:
                print("Error: No se pudo leer el frame de la cámara")
                continue

            print("Frame capturado correctamente.")

            # Convertir el frame de BGR a RGB para Pygame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Rotar la imagen 90 grados en sentido antihorario
            frame_rgb = cv2.rotate(frame_rgb, cv2.ROTATE_90_COUNTERCLOCKWISE)

            # Usar Pygame para mostrar el feed de la cámara
            frame_surface = pygame.surfarray.make_surface(frame_rgb)

            # Limpiar la pantalla antes de dibujar el nuevo frame
            self.pantalla.fill((0, 0, 0))  # Limpiar la pantalla a negro antes de dibujar

            # Mostrar el feed de la cámara en la pantalla (en la parte superior)
            self.pantalla.blit(frame_surface, (0, 0))  # Aquí puedes ajustar la posición si es necesario

            # Procesar el frame con el clasificador de señas
            letra, _ = self.clasificador_senia.procesar_mano(frame)
            if letra:
                print(f"Letra detectada: {letra}")  # Mensaje cuando se detecta una letra
                self.letra_detectada = letra

            # Dibujar las letras que caen después de mostrar el feed de la cámara
            self.dibujar()

            pygame.display.update()  # Actualizar la pantalla de Pygame

            # Pausar ligeramente el bucle para evitar un ciclo infinito rápido
            pygame.time.delay(20)  # Esto ralentiza el bucle del hilo de la cámara

    def mover_letras(self):
        """Mueve las letras hacia abajo y las elimina si salen de la pantalla."""
        for letra in self.letras:
            letra["posicion"][1] += self.velocidad

        # Eliminar letras que salen de la pantalla
        self.letras = [l for l in self.letras if l["posicion"][1] < ALTO]

    def verificar_colision(self):
        """Verifica si la letra detectada coincide con alguna en pantalla."""
        if self.letra_detectada:
            for letra in self.letras:
                if letra["letra"] == self.letra_detectada:
                    self.letras.remove(letra)
                    self.puntuacion += 1
                    self.letra_detectada = None
                    return

    def dibujar(self):
        """Dibuja las letras y la información del juego en pantalla."""
        # Primero, dibujar la imagen de fondo
        self.pantalla.blit(self.fondo, (0, 0))  # Dibujar el fondo


        # Luego, dibujar las letras
        for letra in self.letras:
            texto = self.fuente.render(letra["letra"], True, COLOR_LETRA)
            self.pantalla.blit(texto, letra["posicion"])

        # Dibujar puntuación
        puntuacion_texto = self.fuente.render(f"Puntuación: {self.puntuacion}", True, COLOR_LETRA)
        self.pantalla.blit(puntuacion_texto, (10, 10))

        # Mostrar las vidas
        vidas_texto = self.fuente.render(f"Vidas: {self.vidas}", True, COLOR_LETRA)
        self.pantalla.blit(vidas_texto, (ANCHO - 200, 10))

        pygame.display.flip()

    def dibujar_botones(self):
        """Dibuja los botones en pantalla."""
        # Botón "Empezar"
        pygame.draw.rect(self.pantalla, (0, 255, 0), self.boton_empezar)
        texto_empezar = self.fuente.render("Empezar", True, (255, 255, 255))
        self.pantalla.blit(texto_empezar, (self.boton_empezar.x + 50, self.boton_empezar.y + 10))

        # Botón "Salir"
        pygame.draw.rect(self.pantalla, (255, 0, 0), self.boton_salir)
        texto_salir = self.fuente.render("Salir", True, (255, 255, 255))
        self.pantalla.blit(texto_salir, (self.boton_salir.x + 70, self.boton_salir.y + 10))

    def mostrar_puntuacion_final(self):
        """Muestra la puntuación final cuando el juego termina."""
        self.pantalla.fill((0, 0, 0))  # Limpiar pantalla antes de mostrar el mensaje
        puntuacion_texto = self.fuente.render(f"Puntuación final: {self.puntuacion}", True, COLOR_LETRA)
        self.pantalla.blit(puntuacion_texto, (ANCHO // 2 - 150, ALTO // 2 - 50))

        # Botón de reiniciar o salir
        pygame.draw.rect(self.pantalla, (0, 255, 0), self.boton_empezar)
        texto_empezar = self.fuente.render("Nuevo Juego", True, (255, 255, 255))
        self.pantalla.blit(texto_empezar, (self.boton_empezar.x + 50, self.boton_empezar.y + 10))

        pygame.draw.rect(self.pantalla, (255, 0, 0), self.boton_salir)
        texto_salir = self.fuente.render("Salir", True, (255, 255, 255))
        self.pantalla.blit(texto_salir, (self.boton_salir.x + 70, self.boton_salir.y + 10))

        pygame.display.update()

    def ejecutar(self,resultado_queue=None):
        """Bucle principal del juego."""
          
        self.inicializar() # Controlador para ejecutar el juego

        if not self.jugando:  # Si no se pudo inicializar la cámara
            print("El juego no puede iniciarse debido a problemas con la cámara.")
            return

        self.dibujar_botones()  # Dibuja los botones al inicio
        pygame.display.update()

        # Bandera de estado
        en_juego = False

        while not en_juego:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                # Verificar clic en el botón "Empezar"
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if self.boton_empezar.collidepoint(evento.pos):
                        en_juego = True
                        Thread(target=self.procesar_camara, daemon=True).start()  # Inicia el hilo de la cámara
                        print("Hilo de cámara iniciado.")  # Mensaje para confirmar que el hilo se ha iniciado

                # Verificar clic en el botón "Salir"
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if self.boton_salir.collidepoint(evento.pos):
                        pygame.quit()
                        exit()

            # Dibujar los botones (esto se dibuja continuamente)
            self.dibujar_botones()
            pygame.display.update()

        # Bucle principal del juego
        contador = 0
        while self.jugando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.jugando = False

            # Generar nuevas letras
            if contador % 90 == 0:  # Cada 1.5 segundos (FPS = 60)
                self.generar_letra()

            # Mover letras y verificar colisión
            self.mover_letras()
            self.verificar_colision()

            # Verificar pérdida de vida
            for letra in self.letras:
                if letra["posicion"][1] >= ALTO - 50:  # Si la letra toca el fondo
                    self.letras.remove(letra)
                    self.vidas -= 1  # Restar una vida

            # Verificar si se ha acabado el juego
            if self.vidas <= 0:
                self.jugando = False

            # Dibujar pantalla
            self.dibujar()

            contador += 1
            self.reloj.tick(FPS)

        # Mostrar puntuación final y botones de reiniciar o salir
        self.mostrar_puntuacion_final()

        # Esperar entrada del jugador para reiniciar o salir
        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                # Verificar clic en el botón "Nuevo Juego"
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if self.boton_empezar.collidepoint(evento.pos):
                        juego_nuevo = JuegoLetras()  # Crear una nueva instancia del juego
                        juego_nuevo.ejecutar()  # Iniciar un nuevo juego
                        return  # Salir de la función actual

                # Verificar clic en el botón "Salir"
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if self.boton_salir.collidepoint(evento.pos):
                        pygame.quit()
                        exit()

            # Dibujar los botones
            self.dibujar_botones()
            pygame.display.update()

if __name__ == "__main__":
    print("Ejecutando juego_LC como script independiente.")
    juego2 = JuegoLetras(callback=None)
    juego2.ejecutar()
