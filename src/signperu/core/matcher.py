#src/signperu/core/matcher.py
"""Estrategias de comparación para comparar vectores de características con patrones almacenados.
    Contains a simple HeuristicMatcher (euclidean) and a stub for KNN.
""" 
import math
from typing import List, Tuple

class MatcherStrategy:
    def match(self, vec) -> Tuple[str, float]:
        raise NotImplementedError

class HeuristicMatcher(MatcherStrategy):
    def __init__(self, patterns: List[dict], threshold=0.6):
        # patterns: list of {'letra': 'A', 'vec': [...]}
        self.patterns = patterns
        self.threshold = threshold

    def _dist(self, a, b):
        # simple euclidean distance (assumes same length)
        return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))

    def match(self, vec):
        best = None
        best_score = float('inf')
        for p in self.patterns:
            d = self._dist(vec, p.get('vec', []))
            if d < best_score:
                best_score = d
                best = p
        # convert distance to a confidence-like score (lower distance -> higher confidence)
        if best is None:
            return None, 0.0
        # simple transform: score in [0,1]
        score = max(0.0, 1.0 - (best_score / (self.threshold*2)))
        return best.get('letra'), score

class KNNMatcher(MatcherStrategy):
    def __init__(self, patterns, k=3):
        # stub: you may implement a kNN using scikit-learn on patterns
        self.patterns = patterns
        self.k = k

    def match(self, vec):
        # placeholder returning the first pattern
        if not self.patterns:
            return None, 0.0
        return self.patterns[0].get('letra'), 0.5
