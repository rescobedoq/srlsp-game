#srlsp-game/src/signperu/games/juego_lc.py
# srlsp-game/src/signperu/games/juego_lc.py
"""
Juego "Letras que Caen" refactorizado hacia GameBase.

Requisitos cumplidos:
- Hereda GameBase (start, stop, on_hand_detected)
- No abre la cámara: usa event_bus ("frame_captured", "hand_detected")
- Thread-safe: detecciones y frames recibidas desde hilos distintos
- Dibuja feed de cámara en Pygame (si hay frames)
- Guarda score en DB (si se suministra `db` en constructor)
"""

import pygame
import random
import time
import threading
from collections import deque

import cv2
import numpy as np

from signperu.games.game_base import GameBase

# Configuración visual / juego (ajusta según prefieras)
ANCHO = 800
ALTO = 600
FPS = 30
COLOR_LETRA = (0, 0, 0)
FONT_SIZE = 64
LETTER_SPAWN_INTERVAL = 1.5  # segundos entre letras nuevas
LETTER_SPEED = 2             # píxeles por frame
MAX_LIVES = 20

class JuegoLC(GameBase):
    def __init__(self, event_bus, db=None, config=None, user=None):
        super().__init__(event_bus, db, config, user)

        # Estado del juego
        self.screen = None
        self.clock = None
        self.font = None
        self.running = False
        self.in_play = False  # True cuando el juego principal empezó

        # Letras que caen: lista de dicts {letra, x, y}
        self.letras = []
        self.vidas = MAX_LIVES
        self.puntuacion = 0

        # Detección / frame recibido desde otros hilos
        self._lock = threading.Lock()
        self._latest_frame = None    # numpy array BGR
        self._latest_letter = None   # letra confirmada por detector
        # Para suavizado / debounce simple: mantener ventana de ultimas detecciones
        self._detect_window = deque(maxlen= (config.DETECTOR_CONFIRM_THRESHOLD if config and hasattr(config,"DETECTOR_CONFIRM_THRESHOLD") else 3))

        # Subscripciones al EventBus
        self.event_bus.subscribe("hand_detected", self._on_hand_detected_event)
        self.event_bus.subscribe("frame_captured", self._on_frame_event)

        # Temporizadores internos
        self._last_spawn = 0.0

    # --------------------------
    # Interfaz requerida (GameBase)
    # --------------------------
    def start(self):
        """Arranca la ventana y el bucle principal (bloqueante)."""
        pygame.init()
        pygame.display.set_caption("Letras que Caen - Señales")
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        self.clock = pygame.time.Clock()
        try:
            self.font = pygame.font.Font(None, FONT_SIZE)
        except Exception:
            self.font = pygame.font.SysFont("Arial", FONT_SIZE)

        self.running = True
        self.in_play = False
        self.vidas = MAX_LIVES
        self.puntuacion = 0
        self.letras.clear()
        self._last_spawn = time.time()

        # Pantalla inicial con botones (simple)
        self._main_loop()

    def stop(self):
        """Detener el juego y limpiar recursos."""
        self.running = False
        self.in_play = False
        try:
            self.event_bus.unsubscribe("hand_detected", self._on_hand_detected_event)
            self.event_bus.unsubscribe("frame_captured", self._on_frame_event)
        except Exception:
            pass
        try:
            pygame.quit()
        except Exception:
            pass

    def on_hand_detected(self, letra, frame=None):
        """Implementación de la interfaz GameBase (llamable por terceros)."""
        self._on_hand_detected_event(letra, frame=frame)

    # --------------------------
    # Callbacks EventBus (pueden venir desde hilos de captura/processing)
    # --------------------------
    def _on_frame_event(self, frame):
        """Recibe frame (BGR) y lo guarda para pintarlo en el loop principal."""
        with self._lock:
            # conservamos el último frame (no queremos acumular)
            self._latest_frame = frame

    def _on_hand_detected_event(self, letra, frame=None):
        """
        Cuando el detector publica una letra. Guardamos en ventana para confirmar detección.
        Usamos ventana de confirmación (debounce) para evitar falsos positivos.
        """
        if letra is None:
            return
        with self._lock:
            self._detect_window.append(letra)
            # comprobar si la ventana contiene la misma letra repetida (simple confirm)
            if len(self._detect_window) == self._detect_window.maxlen and len(set(self._detect_window)) == 1:
                # confirmada
                self._latest_letter = self._detect_window[-1]
                # vaciamos ventana para evitar múltiples disparos seguidos
                self._detect_window.clear()

    # --------------------------
    # Lógica del juego
    # --------------------------
    def _spawn_letter(self):
        letra = chr(random.randint(65, 90))
        x = random.randint(30, ANCHO - 30)
        y = -60
        self.letras.append({"letra": letra, "pos": [x, y]})

    def _move_letters(self):
        for l in self.letras:
            l["pos"][1] += LETTER_SPEED
        # eliminar las que salen
        self.letras = [l for l in self.letras if l["pos"][1] < ALTO + 50]

    def _check_collisions(self):
        # si hay letra confirmada, comprobar colisiones
        with self._lock:
            letra_conf = self._latest_letter
            # solo usar una vez
            self._latest_letter = None

        if not letra_conf:
            return

        # buscar letra en pantalla (colisión por igualdad de caracteres, con tolerancia X)
        for l in list(self.letras):
            if l["letra"] == letra_conf:
                try:
                    self.letras.remove(l)
                except ValueError:
                    pass
                self.puntuacion += 1
                return

    # --------------------------
    # Dibujo / utilidades
    # --------------------------
    def _draw_background(self):
        # si hay frame, lo mostramos; si no, fondo negro
        frame = None
        with self._lock:
            frame = self._latest_frame.copy() if self._latest_frame is not None else None

        if frame is not None:
            try:
                # frame viene BGR, convertimos a RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # flip horizontal para espejo
                rgb = cv2.flip(rgb, 1)
                h, w = rgb.shape[:2]
                # adaptamos tamaño al área de juego (ancho ANCHO x alto ALTO)
                # convertimos a surface usando frombuffer (rápido)
                surf = pygame.image.frombuffer(rgb.tobytes(), (w, h), "RGB")
                # escalamos
                surf = pygame.transform.smoothscale(surf, (ANCHO, ALTO))
                self.screen.blit(surf, (0, 0))
            except Exception as e:
                # si falla el dibujo del frame, pintamos fondo negro
                # print("[JuegoLC] error al dibujar frame:", e)
                self.screen.fill((0, 0, 0))
        else:
            self.screen.fill((0, 0, 0))

    def _draw_letters(self):
        for l in self.letras:
            text_surf = self.font.render(l["letra"], True, COLOR_LETRA)
            # poner el texto centrado en x,y
            rect = text_surf.get_rect(center=(l["pos"][0], l["pos"][1]))
            self.screen.blit(text_surf, rect)

    def _draw_hud(self):
        small = pygame.font.Font(None, 28)
        sc_text = small.render(f"Puntuación: {self.puntuacion}", True, (255, 255, 255))
        life_text = small.render(f"Vidas: {self.vidas}", True, (255, 255, 255))
        self.screen.blit(sc_text, (10, 10))
        self.screen.blit(life_text, (ANCHO - 110, 10))

    # --------------------------
    # Bucle principal
    # --------------------------
    def _main_loop(self):
        """
        Bucle principal que maneja: pantalla inicial, espera de START, juego principal, game over.
        """
        # Pantalla inicial con botón "Empezar"
        start_rect = pygame.Rect(ANCHO//2 - 100, ALTO//2 - 25, 200, 50)
        exit_rect = pygame.Rect(ANCHO//2 - 100, ALTO//2 + 40, 200, 50)
        font_btn = pygame.font.Font(None, 36)

        while self.running:
            # pantalla inicial: esperar a que el usuario haga click en "Empezar"
            self.screen.fill((30, 30, 30))
            title = font_btn.render("Letras que Caen - Señales", True, (255,255,255))
            self.screen.blit(title, (ANCHO//2 - title.get_width()//2, ALTO//2 - 120))
            pygame.draw.rect(self.screen, (0, 200, 0), start_rect)
            pygame.draw.rect(self.screen, (200, 0, 0), exit_rect)
            self.screen.blit(font_btn.render("EMPEZAR", True, (255,255,255)), (start_rect.x + 50, start_rect.y + 10))
            self.screen.blit(font_btn.render("SALIR", True, (255,255,255)), (exit_rect.x + 70, exit_rect.y + 10))
            pygame.display.flip()

            # manejar eventos iniciales
            ev = pygame.event.wait()
            if ev.type == pygame.QUIT:
                self.stop()
                return
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(ev.pos):
                    # iniciar juego
                    self.in_play = True
                    break
                elif exit_rect.collidepoint(ev.pos):
                    self.stop()
                    return

        # Bucle principal del juego
        contador = 0
        while self.running and self.in_play:
            start_frame_time = time.time()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    self.in_play = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.running = False
                        self.in_play = False

            # spawn letras según intervalo
            now = time.time()
            if now - self._last_spawn >= LETTER_SPAWN_INTERVAL:
                self._spawn_letter()
                self._last_spawn = now

            # movimiento y colisiones
            self._move_letters()
            self._check_collisions()

            # reducir vidas cuando letras alcanzan fondo
            lost = []
            for l in list(self.letras):
                if l["pos"][1] >= ALTO - 10:
                    try:
                        self.letras.remove(l)
                    except ValueError:
                        pass
                    self.vidas -= 1

            # dibujo
            self._draw_background()
            self._draw_letters()
            self._draw_hud()

            # game over?
            if self.vidas <= 0:
                self.in_play = False
                break

            pygame.display.flip()
            self.clock.tick(FPS)
            contador += 1

        # Mostrar pantalla de puntuación final
        self._game_over_screen()

    def _game_over_screen(self):
        # Guardar score (si db disponible)
        try:
            self.save_score(self.puntuacion, game_name="JuegoLC")
        except Exception:
            pass

        font_big = pygame.font.Font(None, 48)
        font_btn = pygame.font.Font(None, 36)
        replay_rect = pygame.Rect(ANCHO//2 - 110, ALTO//2 + 20, 160, 50)
        exit_rect = pygame.Rect(ANCHO//2 + 10, ALTO//2 + 20, 160, 50)

        while self.running:
            self.screen.fill((10, 10, 10))
            over_text = font_big.render(f"Fin del juego. Puntuación: {self.puntuacion}", True, (255,255,255))
            self.screen.blit(over_text, (ANCHO//2 - over_text.get_width()//2, ALTO//2 - 60))
            pygame.draw.rect(self.screen, (0,200,0), replay_rect)
            pygame.draw.rect(self.screen, (200,0,0), exit_rect)
            self.screen.blit(font_btn.render("Jugar otra vez", True, (255,255,255)), (replay_rect.x + 6, replay_rect.y + 10))
            self.screen.blit(font_btn.render("Salir", True, (255,255,255)), (exit_rect.x + 55, exit_rect.y + 10))
            pygame.display.flip()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    break
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    if replay_rect.collidepoint(ev.pos):
                        # reiniciar estado de juego
                        self.letras.clear()
                        self.vidas = MAX_LIVES
                        self.puntuacion = 0
                        self.in_play = True
                        self._last_spawn = time.time()
                        return self._main_loop()
                    elif exit_rect.collidepoint(ev.pos):
                        self.running = False
                        break
            self.clock.tick(12)

        # cleanup final
        self.stop()
