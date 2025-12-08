# src/signperu/games/clase_ladrillos.py
"""
Lógica del juego 'Ladrillos' (Arkanoid).
Independiente de UI: mantiene estado, reglas, colisiones y generación de niveles.
API principal:
 - reset(level)
 - step(dt)
 - move_paddle_left(), move_paddle_right(), move_paddle_to(x)
 - process_detection(letter)  # p.ej. 'A' -> izquierda, 'B' -> derecha
 - get_state() -> dict con posiciones para dibujar
"""
from typing import List, Tuple, Dict, Optional
import random
import time
import math

# Valores por defecto (coinciden con tu versión original)
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600
PADDLE_W = 80
PADDLE_H = 10
BALL_R = 10

class ClaseLadrillos:
    def __init__(self, width:int=DEFAULT_WIDTH, height:int=DEFAULT_HEIGHT):
        self.width = width
        self.height = height

        # parámetros dinámicos que pueden ajustarse por nivel
        self.paddle_w = PADDLE_W
        self.paddle_h = PADDLE_H
        self.ball_r = BALL_R

        # estado
        self.reset(level=1)

    def reset(self, level:int=1):
        self.level = int(level)
        # Posición paddle (centro X)
        self.paddle_x = self.width // 2
        self.paddle_y = self.height - 20  # distancia del borde inferior
        # Ball
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2 + 200
        # velocidad
        self.ball_vx = random.choice([-6.0, 6.0])
        self.ball_vy = -6.0
        # bloques: lista de dicts {id, x1,y1,x2,y2}
        self.blocks: List[Dict] = []
        self._create_blocks_for_level(self.level)

        # estado de juego
        self.in_play = True
        self.score = 0
        self._last_update = time.time()
        self.lives = 3

        # control de movimiento por detección (simple)
        self._move_target = None  # 'left','right', or None

    # ---------------- generation helpers ----------------
    def _create_blocks_for_level(self, level:int):
        """Genera bloques reutilizando la lógica de diseño (basada en tu versión)."""
        # Generador basado en tu esquema: devolvemos cajas en coordenadas absolutas.
        coords = self._generar_coordenadas(level)
        # bloques como rectángulos (x1,y1,x2,y2)
        self.blocks = []
        for i, (x1, y1, x2, y2) in enumerate(coords):
            self.blocks.append({"id": i, "rect": (x1, y1, x2, y2)})

    def _generar_coordenadas(self, nivel:int):
        """
        Recrea la lógica de generación de coordenadas que tenías en el script original.
        Para simplicidad, vamos a crear filas y columnas y filtrar según patrones por nivel.
        Mantengo formatos similares para usar tus formas.
        """
        # Parámetros de grilla inspirados en código previo
        cols = 23
        rows = 15
        cell_w = 30
        cell_h = 25
        start_x = 20
        start_y = 50

        # construimos lista lineal de ids (1..rows*cols)
        allowed = set()
        # nivel 1: una 'M' aproximada (simplificación)
        if nivel == 1:
            # costados y diagonales
            for r in range(rows):
                for c in range(cols):
                    idx = r * cols + c + 1
                    # criterio simple: columnas 1..6 y 18..23 y diagonales centrales
                    if c < 6 or c >= cols-6:
                        allowed.add(idx)
                    # mediana central
                    if c == cols//2 and r < 6:
                        allowed.add(idx)
            # agregar un patrón M central
            center_col = cols//2
            for r in range(0,6):
                allowed.add(r*cols + (center_col - 3))
                allowed.add(r*cols + (center_col + 3))
        elif nivel == 2:
            # flecha: un triángulo y un rectángulo central
            for r in range(2,13,2):
                span = r
                offset = (cols - span) // 2
                for c in range(offset, offset+span):
                    allowed.add((r)*cols + c + 1)
            # rect central
            for r in range(4,10):
                for c in range((cols//2)-4, (cols//2)+5):
                    allowed.add(r*cols + c + 1)
        else:
            # nivel 3: más denso con huecos para formar una figura aleatoria
            for r in range(rows):
                for c in range(cols):
                    idx = r*cols + c + 1
                    if (r + c) % 2 == 0:
                        allowed.add(idx)
            # añadir algunos agujeros
            for a in range(0, len(allowed)//10):
                if allowed:
                    allowed.pop()

        coords = []
        numero = 1
        for r in range(rows):
            y1 = start_y + r * cell_h
            y2 = y1 + (cell_h - 5)
            x_cursor = start_x
            for c in range(cols):
                if numero in allowed:
                    x1 = x_cursor + 0
                    x2 = x1 + (cell_w - 5)
                    coords.append((x1, y1, x2, y2))
                x_cursor += cell_w
                numero += 1
        return coords

    # ---------------- controls ----------------
    def move_paddle_left(self, amount:int=20):
        self.paddle_x = max(self.paddle_w//2, self.paddle_x - amount)

    def move_paddle_right(self, amount:int=20):
        self.paddle_x = min(self.width - self.paddle_w//2, self.paddle_x + amount)

    def move_paddle_to(self, x:int):
        # centramos la paleta en x
        self.paddle_x = int(max(self.paddle_w//2, min(self.width-self.paddle_w//2, x)))

    def process_detection(self, letra: str):
        """Mapea detecciones a acciones (A->izquierda, B->derecha)."""
        if not letra:
            return
        letra = str(letra).strip().upper()
        if letra == "A":
            self.move_paddle_left()
        elif letra == "B":
            self.move_paddle_right()
        else:
            # otras letras: no acción por ahora
            pass

    # ---------------- physics / step ----------------
    def step(self, dt: Optional[float]=None):
        """Avanza la simulación en dt segundos (si dt es None usa tiempo real)."""
        if not self.in_play:
            return
        if dt is None:
            now = time.time()
            dt = max(1/60.0, now - self._last_update)
            self._last_update = now

        # aplicar movimiento de bola (velocidad en px/frame aproximada)
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        # pared izquierda/derecha
        if self.ball_x - self.ball_r <= 0:
            self.ball_x = self.ball_r
            self.ball_vx = -self.ball_vx
        elif self.ball_x + self.ball_r >= self.width:
            self.ball_x = self.width - self.ball_r
            self.ball_vx = -self.ball_vx

        # techo
        if self.ball_y - self.ball_r <= 0:
            self.ball_y = self.ball_r
            self.ball_vy = -self.ball_vy

        # paleta (AABB collision)
        paddle_left = self.paddle_x - (self.paddle_w // 2)
        paddle_right = self.paddle_x + (self.paddle_w // 2)
        paddle_top = self.paddle_y - (self.paddle_h // 2)
        paddle_bottom = self.paddle_y + (self.paddle_h // 2)

        if (self.ball_x + self.ball_r >= paddle_left and self.ball_x - self.ball_r <= paddle_right and
            self.ball_y + self.ball_r >= paddle_top and self.ball_y - self.ball_r <= paddle_bottom and
            self.ball_vy > 0):
            # rebote simple: invertir vy y ajustar vx según offset relativo
            self.ball_vy = -abs(self.ball_vy)
            hit_offset = (self.ball_x - self.paddle_x) / (self.paddle_w / 2)  # -1..1
            self.ball_vx += hit_offset * 2.0  # ajustar ángulo
            # limitar vx razonablemente
            max_vx = 10.0
            self.ball_vx = max(-max_vx, min(max_vx, self.ball_vx))

        # bloques: comprobar colisión con cada bloque (AABB)
        for b in list(self.blocks):
            x1,y1,x2,y2 = b["rect"]
            if (self.ball_x + self.ball_r >= x1 and self.ball_x - self.ball_r <= x2 and
                self.ball_y + self.ball_r >= y1 and self.ball_y - self.ball_r <= y2):
                # colisión: eliminar bloque y rebotar según lado de impacto
                try:
                    self.blocks.remove(b)
                except ValueError:
                    pass
                self.score += 1
                # determinar si rebota vertical u horizontal (comprobación simple)
                # comparo profundidad de solapamiento en X e Y
                overlap_x = min(self.ball_x + self.ball_r - x1, x2 - (self.ball_x - self.ball_r))
                overlap_y = min(self.ball_y + self.ball_r - y1, y2 - (self.ball_y - self.ball_r))
                if overlap_x < overlap_y:
                    self.ball_vx = -self.ball_vx
                else:
                    self.ball_vy = -self.ball_vy
                break

        # comprobar pérdida (bola bajo el fondo)
        if self.ball_y - self.ball_r > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self.in_play = False
            else:
                # reubicar bola y paleta para continuar
                self.ball_x = self.width // 2
                self.ball_y = self.height // 2 + 200
                self.ball_vx = random.choice([-6.0, 6.0])
                self.ball_vy = -6.0

        # comprobar victoria (sin bloques)
        if not self.blocks:
            self.in_play = False

    # ---------------- getters para UI ----------------
    def get_state(self) -> Dict:
        """Estado minimal para dibujar en UI."""
        return {
            "paddle": (self.paddle_x, self.paddle_y, self.paddle_w, self.paddle_h),
            "ball": (self.ball_x, self.ball_y, self.ball_r),
            "blocks": [b["rect"] for b in self.blocks],
            "score": self.score,
            "lives": self.lives,
            "in_play": self.in_play,
            "level": self.level
        }
