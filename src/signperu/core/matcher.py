#srlsp-game/src/signperu/core/matcher.py
""" Este módulo proporciona:
- MatcherStrategy: interfaz base.
- HeuristicMatcher: comparación por distancia (euclidiana o coseno) con transformación a score [0,1].
- KNNMatcher: implementación opcional basada en scikit-learn (si está instalado).
Notas sobre 'threshold':
- En HeuristicMatcher, `threshold` representa la distancia máxima "útil" para considerar coincidencias.
  Se transforma a score con la fórmula: score = max(0.0, 1.0 - (dist / threshold))
  - Si dist == 0.0 -> score = 1.0 (coincidencia perfecta)
  - Si dist >= threshold -> score = 0.0 (no hay coincidencia aceptable)
- Ajusta `threshold` en base a la escala de tus vectores (normalizados o no).
  - Si tus vectores están normalizados por magnitud (norm L2 = 1), distancias euclidianas típicas
    estarán en [0, 2]. Umbrales iniciales sugeridos: 0.2 - 0.8 (probar y calibrar).
  - Si usas coseno, la distancia coseno = 1 - cosine_similarity; valores cercanos a 0 son mejores.
"""
import math
from typing import List, Tuple, Callable, Optional

# Intentamos importar sklearn para KNN; si no está, KNNMatcher hará fallback.
try:
    from sklearn.neighbors import KNeighborsClassifier
    import numpy as np
except Exception:
    KNeighborsClassifier = None
    np = None

class MatcherStrategy:
    """Interfaz base para estrategias de matching."""
    def match(self, vec) -> Tuple[Optional[str], float]:
        """Dado un vector `vec` devuelve (letra, score) donde score ∈ [0.0, 1.0]."""
        raise NotImplementedError


def _euclidean_distance(a: List[float], b: List[float]) -> float:
    """Distancia euclidiana entre vectores (asume misma longitud)."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _cosine_distance(a: List[float], b: List[float]) -> float:
    """Distancia basada en coseno: 0 = idénticos, 1 = ortogonales (devuelve 1 - cos_sim)."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 1.0
    cos_sim = dot / (na * nb)
    # limitar por seguridad
    cos_sim = max(-1.0, min(1.0, cos_sim))
    return 1.0 - cos_sim


class HeuristicMatcher(MatcherStrategy):
    """
    Comparador heurístico que busca el patrón con menor distancia y transforma la distancia
    en una confianza (score) en [0,1].

    Parámetros:
        patterns: lista de dicts {'letra': 'A', 'vec': [...]}.
        threshold: distancia a partir de la cual consideramos score == 0.0.
                   Ajustar según normalización de vectores.
        dist_fn: función de distancia a usar (por defecto euclidiana). Puede ser _euclidean_distance o _cosine_distance.
    """

    def __init__(self, patterns: List[dict], threshold: float = 0.6, dist_fn: Callable = _euclidean_distance):
        self.patterns = patterns or []
        self.threshold = float(threshold)
        self.dist_fn = dist_fn

        # Validación inicial: comprobar que todos los patterns tienen 'vec' y misma longitud
        self._expected_len = None
        if self.patterns:
            for p in self.patterns:
                vec = p.get('vec')
                if vec is None:
                    raise ValueError("Cada patrón debe tener la clave 'vec' con la lista de características.")
                if self._expected_len is None:
                    self._expected_len = len(vec)
                elif len(vec) != self._expected_len:
                    raise ValueError(f"Longitudes de 'vec' inconsistentes en patterns: "
                                     f"{len(vec)} != {self._expected_len}")

    def _validate_input(self, vec: List[float]):
        if self._expected_len is not None and len(vec) != self._expected_len:
            raise ValueError(f"Vector de entrada tiene longitud {len(vec)} pero se esperaba {self._expected_len}.")

    def _distance_to_score(self, dist: float) -> float:
        """Convierte distancia en score [0,1] usando threshold como distancia máxima útil."""
        if dist <= 0:
            return 1.0
        if dist >= self.threshold:
            return 0.0
        # Transformación lineal simple; puedes cambiar por otra curva (ej. exponencial)
        score = 1.0 - (dist / self.threshold)
        return max(0.0, min(1.0, score))

    def match(self, vec: List[float]) -> Tuple[Optional[str], float]:
        """Devuelve (letra, score). Si no hay patrones, devuelve (None, 0.0)."""
        if not self.patterns:
            return None, 0.0

        self._validate_input(vec)

        best = None
        best_dist = float('inf')
        for p in self.patterns:
            pvec = p.get('vec', [])
            # por seguridad, ignorar patrones sin vec o con longitud distinta
            if not pvec or (self._expected_len is not None and len(pvec) != self._expected_len):
                continue
            d = self.dist_fn(vec, pvec)
            if d < best_dist:
                best_dist = d
                best = p

        if best is None:
            return None, 0.0

        score = self._distance_to_score(best_dist)
        return best.get('letra'), score


class KNNMatcher(MatcherStrategy):
    """
    Matcher basado en KNN (scikit-learn).
    - Si sklearn no está disponible, hace fallback a una versión simple basada en HeuristicMatcher.
    """

    def __init__(self, patterns: List[dict], k: int = 3):
        self.patterns = patterns or []
        self.k = int(k)

        # Validación y preparación de datos si sklearn está disponible
        if self.patterns:
            # comprobar consistencia de longitud de vectores
            lengths = {len(p['vec']) for p in self.patterns if 'vec' in p and p['vec'] is not None}
            if len(lengths) > 1:
                raise ValueError("Los vectores en 'patterns' deben tener todos la misma longitud para KNN.")
            self._expected_len = next(iter(lengths)) if lengths else None
        else:
            self._expected_len = None

        if KNeighborsClassifier is not None and np is not None and self.patterns:
            X = np.array([p['vec'] for p in self.patterns])
            y = np.array([p['letra'] for p in self.patterns])
            self._knn = KNeighborsClassifier(n_neighbors=min(self.k, len(self.patterns)))
            self._knn.fit(X, y)
        else:
            # fallback: usar HeuristicMatcher sobre los mismos patterns
            self._knn = None
            self._fallback = HeuristicMatcher(self.patterns, threshold=0.6)

    def match(self, vec: List[float]) -> Tuple[Optional[str], float]:
        """Devuelve (letra, score). Si KNN está disponible retorna predicción y confianza aproximada."""
        if not self.patterns:
            return None, 0.0

        if self._knn is not None:
            # predict_proba puede no estar disponible si las clases únicas; manejar excepciones
            try:
                pred = self._knn.predict([vec])[0]
                # intentar obtener probabilidad; si falla, devolver 0.5 por defecto
                proba = 0.5
                if hasattr(self._knn, "predict_proba"):
                    probs = self._knn.predict_proba([vec])[0]
                    # mapear la probabilidad correspondiente a la clase predicha
                    classes = self._knn.classes_
                    idx = list(classes).index(pred)
                    proba = float(probs[idx])
                return pred, float(proba)
            except Exception:
                # en caso de fallo, fallback heurístico
                return self._fallback.match(vec)
        else:
            # Fallback sin sklearn
            return self._fallback.match(vec)
