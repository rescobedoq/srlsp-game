#src/signperu/core/features.py
"""Ayudas para la extracción de características:
    Converts MediaPipe landmarks into a normalized feature vector suitable for matching.
"""
import math

def extract_features(hand_landmarks):
    """Given a MediaPipe hand_landmarks object, return a simple normalized vector.
    This is a placeholder — adapt as needed (distances, angles, relative coords).
    """
    # hand_landmarks.landmark is iterable of 21 points with x,y,z
    pts = [(p.x, p.y, p.z) for p in hand_landmarks.landmark]
    # Normalize by wrist (0)
    base_x, base_y, base_z = pts[0]
    vec = []
    for (x,y,z) in pts:
        vec.append(x - base_x)
        vec.append(y - base_y)
        vec.append(z - base_z)
    # Optionally normalize magnitude
    norm = math.sqrt(sum(v*v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec
