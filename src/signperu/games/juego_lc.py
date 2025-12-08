#srlsp-game/src/signperu/games/juego_lc.py
# src/signperu/games/juego_lc.py
"""
UI / Pygame wrapper para el juego "Letras que Caen".
Usa LetrasLogic (separado en clase) para la física / estado.
"""
import pygame
import time
import threading
import cv2

from signperu.games.game_base import GameBase
from signperu.games.clase_lc import LetrasLogic

# Layout constants (ajusta si quieres)
ANCHO = 1000
ALTO = 600
CAMERA_PANEL_W = 500
CAMERA_PANEL_H = 370
CAMERA_PANEL_POS = (10, 80)
GAME_AREA_X = CAMERA_PANEL_W + 30
GAME_AREA_W = ANCHO - GAME_AREA_X - 10

FPS = 30
FONT_SIZE = 64
ENTRY_BOX_POS = (10, 470)
ENTRY_BOX_SIZE = (CAMERA_PANEL_W, 110)

class JuegoLC(GameBase):
    def __init__(self, event_bus, db=None, config=None, user=None):
        super().__init__(event_bus, db, config, user)
        # lógica separada
        cfg = config or type("C", (), {})()
        spawn_interval = getattr(cfg, "LETTER_SPAWN_INTERVAL", 1.5)
        letter_speed = getattr(cfg, "LETTER_SPEED", 2.0)
        max_lives = getattr(cfg, "MAX_LIVES", 20)
        detect_confirm = getattr(cfg, "DETECTOR_CONFIRM_THRESHOLD", 3)

        self.logic = LetrasLogic(width=GAME_AREA_W, height=ALTO,
                                 spawn_interval=spawn_interval,
                                 letter_speed=letter_speed,
                                 max_lives=max_lives,
                                 detect_confirm=detect_confirm)

        # subscripciones
        self.event_bus.subscribe("hand_detected", self._on_hand_detected_event)
        self.event_bus.subscribe("frame_captured", self._on_frame_event)

        # UI state
        self.screen = None
        self.clock = None
        self.font = None
        self.running = False
        self.in_play = False
        self._lock = threading.Lock()
        self._latest_frame = None  # BGR numpy array

    def start(self):
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
        self.logic.reset()
        self._main_loop()

    def stop(self):
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
        # interfaz por si alguien quiere llamar directamente (p. ej. tests)
        self.logic.push_detected(letra)

    # --------------- EventBus callbacks ----------------
    def _on_frame_event(self, frame):
        with self._lock:
            self._latest_frame = frame

    def _on_hand_detected_event(self, *args, **kwargs):
        """
        Handler flexible: extrae letra como string (si la hay) y la pasa a la lógica.
        Evita errores si vienen kwargs extra (landmarks, etc).
        """
        letra = None
        # Chequeo sencillo: buscar primer str en args o kwargs["letra"/"letter"]
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
            self.logic.push_detected(letra)

    # --------------- Dibujo ----------------
    def _draw_camera_panel(self):
        frame = None
        with self._lock:
            frame = self._latest_frame.copy() if self._latest_frame is not None else None

        if frame is not None:
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb = cv2.flip(rgb, 1)
                h, w = rgb.shape[:2]
                surf = pygame.image.frombuffer(rgb.tobytes(), (w, h), "RGB")
                surf = pygame.transform.smoothscale(surf, (CAMERA_PANEL_W, CAMERA_PANEL_H))
                self.screen.blit(surf, CAMERA_PANEL_POS)
            except Exception:
                pygame.draw.rect(self.screen, (20,20,20), (CAMERA_PANEL_POS[0], CAMERA_PANEL_POS[1], CAMERA_PANEL_W, CAMERA_PANEL_H))
        else:
            pygame.draw.rect(self.screen, (20,20,20), (CAMERA_PANEL_POS[0], CAMERA_PANEL_POS[1], CAMERA_PANEL_W, CAMERA_PANEL_H))

    def _draw_detection_box(self):
        x,y = ENTRY_BOX_POS
        w,h = ENTRY_BOX_SIZE
        pygame.draw.rect(self.screen, (0,0,0), (x,y,w,h))
        pygame.draw.rect(self.screen, (255,255,255), (x,y,w,h), 3)
        small = pygame.font.Font(None, 20)
        guide = small.render("Letra detectada (conf.):", True, (200,200,200))
        self.screen.blit(guide, (x+8, y+6))
        last = self.logic.get_last_shown_letter() or " "
        big_font = pygame.font.Font(None, 100)
        text_surf = big_font.render(last, True, (255,255,255))
        rect = text_surf.get_rect(center=(x + w//2, y + h//2 + 8))
        self.screen.blit(text_surf, rect)

    def _draw_game_area(self):
        # fondo del área de juego
        game_area_rect = (GAME_AREA_X, 0, GAME_AREA_W, ALTO)
        pygame.draw.rect(self.screen, (240, 240, 240), game_area_rect)
        # dibujar letras (la lógica mantiene posiciones relativas; las convertimos al area)
        for item in self.logic.get_letters():
            lx = GAME_AREA_X + int(item["pos"][0])
            ly = int(item["pos"][1])
            text_surf = self.font.render(item["letra"], True, (0,0,0))
            rect = text_surf.get_rect(center=(lx, ly))
            self.screen.blit(text_surf, rect)

        # HUD
        small = pygame.font.Font(None, 28)
        sc_text = small.render(f"Puntuación: {self.logic.get_score()}", True, (255,255,255))
        life_text = small.render(f"Vidas: {self.logic.get_lives()}", True, (255,255,255))
        self.screen.blit(sc_text, (10,10))
        self.screen.blit(life_text, (ANCHO - 110, 10))

    # --------------- Loop ----------------
    def _main_loop(self):
        start_rect = pygame.Rect(ANCHO//2 - 100, ALTO//2 - 25, 200, 50)
        exit_rect = pygame.Rect(ANCHO//2 - 100, ALTO//2 + 40, 200, 50)
        font_btn = pygame.font.Font(None, 36)

        while self.running:
            # pantalla inicial
            self.screen.fill((30,30,30))
            title = font_btn.render("Letras que Caen - Señales", True, (255,255,255))
            self.screen.blit(title, (ANCHO//2 - title.get_width()//2, ALTO//2 - 120))
            pygame.draw.rect(self.screen, (0,200,0), start_rect)
            pygame.draw.rect(self.screen, (200,0,0), exit_rect)
            self.screen.blit(font_btn.render("EMPEZAR", True, (255,255,255)), (start_rect.x + 50, start_rect.y + 10))
            self.screen.blit(font_btn.render("SALIR", True, (255,255,255)), (exit_rect.x + 70, exit_rect.y + 10))
            pygame.display.flip()

            ev = pygame.event.wait()
            if ev.type == pygame.QUIT:
                self.stop()
                return
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(ev.pos):
                    self.in_play = True
                    break
                elif exit_rect.collidepoint(ev.pos):
                    self.stop()
                    return

        # loop principal
        while self.running and self.in_play:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    self.in_play = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.running = False
                        self.in_play = False

            # actualizar lógica (spawn/move/vidas)
            self.logic.tick()

            # dibujo
            self.screen.fill((0,0,0))
            self._draw_camera_panel()
            self._draw_detection_box()
            self._draw_game_area()

            pygame.display.flip()
            self.clock.tick(FPS)

            # game over?
            if self.logic.is_game_over():
                break

        # game over UI / guardar score
        try:
            self.save_score(self.logic.get_score(), game_name="JuegoLC")
        except Exception:
            pass
        # simple pantalla final
        self._game_over_screen()

    def _game_over_screen(self):
        font_big = pygame.font.Font(None, 48)
        font_btn = pygame.font.Font(None, 36)
        replay_rect = pygame.Rect(ANCHO//2 - 110, ALTO//2 + 20, 160, 50)
        exit_rect = pygame.Rect(ANCHO//2 + 10, ALTO//2 + 20, 160, 50)

        while self.running:
            self.screen.fill((10,10,10))
            over_text = font_big.render(f"Fin del juego. Puntuación: {self.logic.get_score()}", True, (255,255,255))
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
                        self.logic.reset()
                        self.in_play = True
                        return self._main_loop()
                    elif exit_rect.collidepoint(ev.pos):
                        self.running = False
                        break
            self.clock.tick(12)

        self.stop()
