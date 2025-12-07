#srlsp-game/src/signperu/games/juego_AH.py
# Juego simple: cuando detecta la letra esperada cuenta éxito
from signperu.games.game_base import Game

# src/signperu/games/juego_AH.py
# Juego del ahorcado (versión refactorizada para la arquitectura del proyecto)
# - Subclase de Game
# - Carga palabras desde archivo "PALABRAS" (mismo directorio) o usa lista por defecto
# - Thread-safe: protege estados con Lock (on_detection será llamado desde un hilo distinto)
# - No modifica UI directamente: publica eventos en EventBus ("game_update", "game_over")
# - Persiste score en DB (si se proporciona DB en app_context)
import os
import random
import threading
from typing import List, Dict, Optional

from signperu.games.game_base import Game
from signperu.utils.logger import get_logger

LOGGER = get_logger(__name__)

DEFAULT_PALABRAS = [
    "PERU", "AMIGO", "FAMILIA", "COMPUTADORA", "EDUCACION", "SALUD",
    "INCLUSION", "SEÑAS", "APRENDIZAJE", "JUEGO"
]

class JuegoAH(Game):
    """
    Juego del Ahorcado orientado a usarse con EventBus:
    - Se espera que la app registre: event_bus.subscribe("detection", lambda t: juego.on_detection(t))
    - El juego publica actualizaciones mediante event_bus.publish("game_update", payload)
      y cuando termina publica event_bus.publish("game_over", payload)
    """
    def __init__(self, app_context: Dict, palabras_path: Optional[str] = None, max_oportunidades: int = 6):
        """
        app_context: dict con al menos event_bus, db (opcional), user (opcional)
        palabras_path: ruta al fichero con palabras (una por línea). Si None, busca archivo 'PALABRAS'
                       en el mismo directorio del módulo; si no existe usa DEFAULT_PALABRAS.
        """
        super().__init__(app_context)
        self.max_oportunidades = max_oportunidades
        self.event_bus = app_context.get("event_bus")
        self.db = app_context.get("db")
        self.user = app_context.get("user")
        self._lock = threading.Lock()

        # cargar palabras
        if palabras_path:
            self.palabras = self._cargar_palabras_desde_archivo(palabras_path)
        else:
            # buscar archivo "PALABRAS" en el mismo folder que este fichero
            base_path = os.path.dirname(__file__)
            candidate = os.path.join(base_path, "PALABRAS")
            if os.path.exists(candidate):
                self.palabras = self._cargar_palabras_desde_archivo(candidate)
            else:
                # fallback
                self.palabras = list(DEFAULT_PALABRAS)

        # estado del juego
        self.palabra: str = ""
        self.palabra_deletreada: List[str] = []
        self.letrero_juego: List[str] = []
        self.letras_usadas: List[str] = []
        self.letras_necesarias: List[str] = []
        self.letras_adivinadas: List[str] = []
        self.oportunidades: int = self.max_oportunidades
        self.jugador_vivo: bool = True
        self.victoria: bool = False

    # --------------------------
    # Carga de palabras
    # --------------------------
    def _cargar_palabras_desde_archivo(self, ruta: str) -> List[str]:
        palabras = []
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                for linea in f:
                    p = linea.strip().upper()
                    if p:
                        palabras.append(p)
        except Exception as e:
            LOGGER.exception(f"No se pudo leer el archivo de palabras '{ruta}': {e}")
        if not palabras:
            LOGGER.warning("Lista de palabras vacía; usando lista por defecto.")
            return list(DEFAULT_PALABRAS)
        return palabras

    # --------------------------
    # Estado público / utilidades
    # --------------------------
    def nuevojuego(self):
        """Inicializa un nuevo juego seleccionando una palabra aleatoria."""
        with self._lock:
            self.palabra = random.choice(self.palabras)
            self.palabra_deletreada = [c for c in self.palabra]
            self.letrero_juego = [(" " if c.isspace() else "_") for c in self.palabra_deletreada]
            self.letras_usadas = []
            self.oportunidades = self.max_oportunidades
            self.jugador_vivo = True
            # letras necesarias (sin repeticiones) - ignoramos espacios
            letras = []
            for c in self.palabra_deletreada:
                if not c.isspace() and c not in letras:
                    letras.append(c)
            self.letras_necesarias = letras
            self.letras_adivinadas = []
            self.victoria = False

            LOGGER.info(f"[JuegoAH] Nuevo juego. Palabra seleccionada (oculta): '{self.palabra}'")
            # publicar primer estado para que UI se actualice
            self._publicar_update()

    def get_state(self) -> Dict:
        """Devuelve un dict serializable con el estado actual del juego."""
        with self._lock:
            return {
                "palabra": self.palabra,
                "letrero": "".join(self.letrero_juego),
                "letrero_list": list(self.letrero_juego),
                "letras_usadas": list(self.letras_usadas),
                "oportunidades": self.oportunidades,
                "jugador_vivo": self.jugador_vivo,
                "victoria": self.victoria,
                "letras_necesarias": list(self.letras_necesarias),
                "letras_adivinadas": list(self.letras_adivinadas)
            }

    # --------------------------
    # Lógica de juego
    # --------------------------
    def jugar_letra(self, letra_entrada: str) -> bool:
        """
        Procesa una jugada (una letra). Retorna True si la jugada fue válida (nueva letra),
        False si la letra ya fue usada o la entrada inválida.
        No hace UI aquí; solo actualiza estado y publica eventos en EventBus.
        """
        if not letra_entrada:
            return False
        try:
            letra = str(letra_entrada).strip().upper()[0]
        except Exception:
            return False

        # Permitimos caracteres alfabéticos y Ñ
        if not (letra.isalpha() or letra == "Ñ"):
            return False

        with self._lock:
            if letra in self.letras_usadas:
                # letra ya jugada
                LOGGER.debug(f"[JuegoAH] Letra ya usada: {letra}")
                return False

            self.letras_usadas.append(letra)

            if letra in self.letras_necesarias:
                # acierto
                if letra not in self.letras_adivinadas:
                    self.letras_adivinadas.append(letra)
                self._actualizar_letrero()
                # comprobar victoria
                if len(self.letras_adivinadas) == len(self.letras_necesarias):
                    self.victoria = True
                    self.jugador_vivo = True
                    LOGGER.info(f"[JuegoAH] Victoria! palabra='{self.palabra}'")
                    # persistir resultado victoria (score)
                    self._persistir_resultado(victoria=True)
                    # publicar evento game_over
                    self._publicar_game_over()
                else:
                    # publicar update normal
                    self._publicar_update()
            else:
                # fallo: decrementar oportunidades
                self.oportunidades -= 1
                LOGGER.info(f"[JuegoAH] Fallo con letra '{letra}'. Oportunidades restantes: {self.oportunidades}")
                if self.oportunidades <= 0:
                    self.jugador_vivo = False
                    self.victoria = False
                    LOGGER.info(f"[JuegoAH] Juego terminado. Perdió. Palabra: '{self.palabra}'")
                    # persistir resultado (derrota)
                    self._persistir_resultado(victoria=False)
                    self._publicar_game_over()
                else:
                    self._publicar_update()

            return True

    def on_detection(self, token: Optional[str]):
        """
        Método que será invocado por el ProcessingThread (hilo secundario)
        cuando llegue una detección (token). Debe ser seguro con hilos.
        """
        if token is None:
            return
        # no hacemos nada si el juego no está activo
        with self._lock:
            if not self.running:
                LOGGER.debug("[JuegoAH] on_detection recibido pero juego no está en ejecución.")
                return

        # delegar a jugar_letra, pero sin sostener lock externo
        valid = self.jugar_letra(token)
        if not valid:
            LOGGER.debug(f"[JuegoAH] Detección '{token}' no fue una jugada válida (quizá repetida).")

    def _actualizar_letrero(self):
        """Reconstruye letrero_juego a partir de letras_adivinadas y palabra_deletreada."""
        self.letrero_juego.clear()
        for letra in self.palabra_deletreada:
            if letra in self.letras_adivinadas:
                self.letrero_juego.append(letra)
            elif letra.isspace():
                self.letrero_juego.append(" ")
            else:
                self.letrero_juego.append("_")

    # --------------------------
    # Integración con Game base
    # --------------------------
    def start(self):
        """Marca el juego como iniciado y publica estado inicial."""
        with self._lock:
            super().start()
            # si no hay palabra seleccionada, iniciar nuevo juego
            if not self.palabra:
                self.nuevojuego()
            # publicar estado actual para UI
            self._publicar_update()
            LOGGER.debug("[JuegoAH] start() llamado.")

    def stop(self):
        """Marca el juego como detenido."""
        with self._lock:
            super().stop()
            LOGGER.debug("[JuegoAH] stop() llamado.")

    # --------------------------
    # Persistencia y eventos
    # --------------------------
    def _persistir_resultado(self, victoria: bool):
        """Guarda en DB el resultado de la partida si DB y user están disponibles."""
        try:
            if not self.db or not self.user:
                LOGGER.debug("[JuegoAH] DB o user no disponibles; no se persiste resultado.")
                return
            # score simple: 1 para victoria, 0 para derrota; puedes cambiar lógica de puntuación
            score = 1 if victoria else 0
            username = self.user.get("username") if isinstance(self.user, dict) else None
            user_id = None
            if username and hasattr(self.db, "get_user"):
                u = self.db.get_user(username)
                if u:
                    user_id = u.get("id") if isinstance(u, dict) else u["id"]
            # si user_id no disponible, intentar obtener user["id"]
            if not user_id and isinstance(self.user, dict) and "id" in self.user:
                user_id = self.user["id"]

            if not user_id:
                LOGGER.debug("[JuegoAH] No se pudo determinar user_id para persistencia.")
                return

            self.db.save_score(user_id, "AH", score, details=f"oportunidades_restantes={self.oportunidades}")
            LOGGER.info(f"[JuegoAH] Resultado persistido. user_id={user_id}, victoria={victoria}")
        except Exception as e:
            LOGGER.exception(f"[JuegoAH] Error persistiendo resultado: {e}")

    def _publicar_update(self):
        """Publica evento 'game_update' con el estado actual (no bloqueante)."""
        try:
            if self.event_bus:
                payload = self.get_state()
                # añadir metadatos: tipo de juego
                payload["game"] = "AH"
                self.event_bus.publish("game_update", payload)
        except Exception:
            LOGGER.exception("[JuegoAH] Error publicando game_update")

    def _publicar_game_over(self):
        """Publica evento 'game_over' cuando la partida finaliza."""
        try:
            if self.event_bus:
                payload = self.get_state()
                payload["game"] = "AH"
                payload["final"] = True
                self.event_bus.publish("game_over", payload)
        except Exception:
            LOGGER.exception("[JuegoAH] Error publicando game_over")
