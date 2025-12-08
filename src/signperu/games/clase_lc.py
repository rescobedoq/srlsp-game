# src/signperu/games/clase_lc.py
"""
Lógica del juego "Letras que Caen".
Responsabilidades:
- Mantener lista de letras (posición, char)
- Generar (spawn), mover y limpiar letras
- Comprobar colisiones cuando llega una letra confirmada por detector
- Ventana de confirmación (debounce) para detecciones
- Exponer estado para que la UI lo dibuje
Diseñado para ser independiente de Pygame / UI.
"""

from collections import deque
import time
import random
from typing import List, Dict, Optional

class LetrasLogic:
    def __init__(self, *,
                 width:int=800, height:int=600,
                 spawn_interval:float=1.5, letter_speed:float=2.0,
                 max_lives:int=20, detect_confirm:int=3):
        # Tamaño lógico (usado para límites)
        self.width = width
        self.height = height

        # parámetros de juego
        self.spawn_interval = float(spawn_interval)
        self.letter_speed = float(letter_speed)
        self.max_lives = int(max_lives)

        # estado dinámico
        self.letras: List[Dict] = []   # cada item: {"letra": "A", "pos":[x,y]}
        self.vidas = self.max_lives
        self.puntuacion = 0

        # temporizadores
        self._last_spawn_ts = time.time()

        # debounce/confirm window para detecciones
        self.detect_window = deque(maxlen=max(1, int(detect_confirm)))
        # letra confirmada lista para consumir por la lógica
        self._latest_confirmed: Optional[str] = None

        # último caracter que se mostró/consumió (útil para UI)
        self.last_shown_letter: Optional[str] = None

    # --------------- API para UI / loop ----------------
    def reset(self):
        self.letras.clear()
        self.vidas = self.max_lives
        self.puntuacion = 0
        self._last_spawn_ts = time.time()
        self.detect_window.clear()
        self._latest_confirmed = None
        self.last_shown_letter = None

    def tick(self, now:float=None):
        """
        Actualiza estado: spawn, mover letras, procesar confirmadas y vidas.
        Debe llamarse desde el bucle principal periódicamente.
        """
        if now is None:
            now = time.time()

        # spawn
        if now - self._last_spawn_ts >= self.spawn_interval:
            self._spawn_random()
            self._last_spawn_ts = now

        # mover letras
        for l in self.letras:
            l["pos"][1] += self.letter_speed

        # eliminar letras fuera y restar vidas
        survived = []
        for l in self.letras:
            if l["pos"][1] < self.height + 50:
                survived.append(l)
            else:
                # alcanzó fondo => perder vida
                self.vidas -= 1
        self.letras = survived

        # si hay letra confirmada, procesarla
        if self._latest_confirmed:
            self._consume_confirmed(self._latest_confirmed)
            self._latest_confirmed = None

    def is_game_over(self) -> bool:
        return self.vidas <= 0

    # --------------- spawn / movimiento / colisiones ----------------
    def _spawn_random(self):
        letter = chr(random.randint(65, 90))
        x = random.randint(30, max(30, self.width - 30))
        y = -60
        self.letras.append({"letra": letter, "pos": [x, y]})

    def _consume_confirmed(self, letra:str):
        """
        Busca una letra igual en pantalla; si la encuentra la elimina y suma punto.
        Si no, no hace nada (podrías penalizar si quieres).
        """
        for l in list(self.letras):
            if l["letra"] == letra:
                try:
                    self.letras.remove(l)
                except ValueError:
                    pass
                self.puntuacion += 1
                self.last_shown_letter = letra
                return
        # si no encontró, mostrar igualmente (feedback), pero no puntuar
        self.last_shown_letter = letra

    # --------------- detección / debounce ----------------
    def push_detected(self, letra: str):
        """
        Empujar una nueva detección (string). La lógica se encarga de confirmar
        cuando la ventana se llena con la misma letra.
        """
        if not letra:
            return
        letra = letra.strip().upper()
        if not letra:
            return
        # usar solo primer caracter alfabético
        if len(letra) > 1:
            found = None
            for ch in letra:
                if ch.isalpha() or ch == "Ñ":
                    found = ch
                    break
            letra = found if found else letra[0]
        if not (letra.isalpha() or letra == "Ñ"):
            return

        self.detect_window.append(letra)
        if len(self.detect_window) == self.detect_window.maxlen:
            items = list(self.detect_window)
            if all(x == items[0] for x in items):
                # confirmación
                self._latest_confirmed = items[-1]
                self.detect_window.clear()

    # --------------- getters para UI ----------------
    def get_letters(self):
        return list(self.letras)   # copia superficial

    def get_score(self):
        return self.puntuacion

    def get_lives(self):
        return self.vidas

    def get_last_shown_letter(self):
        return self.last_shown_letter
