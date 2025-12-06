#srlsp-game/src/signperu/core/features.py
"""Ayudas para la extracción de características:
    Converts MediaPipe landmarks into a normalized feature vector suitable for matching.
Expected output: list[float] with length = NUM_LANDMARKS * 3 = 63
Order: [x0-base_x, y0-base_y, z0-base_z, x1-base_x, y1-base_y, z1-base_z, ..., x20-base_x, y20-base_y, z20-base_z]
"""
from typing import List
import math

NUM_LANDMARKS = 21
COORDS_PER_LM = 3
EXPECTED_LENGTH = NUM_LANDMARKS * COORDS_PER_LM  # 63

def extract_features(hand_landmarks, normalize: bool = True) -> List[float]:
    """
    Convert a MediaPipe hand_landmarks object into a normalized vector.

    Args:
        hand_landmarks: MediaPipe hand_landmarks object having .landmark[0..20] with .x,.y,.z floats.
        normalize: If True, normalize vector by its L2 norm (magnitude).

    Returns:
        vec: list of floats of length EXPECTED_LENGTH (63).
    """
    # Extract (x,y,z) tuples
    pts = [(p.x, p.y, p.z) for p in hand_landmarks.landmark]

    if len(pts) != NUM_LANDMARKS:
        # Defensive: if input is unexpected, try to proceed but warn via exception
        raise ValueError(f"hand_landmarks must contain {NUM_LANDMARKS} points (got {len(pts)})")

    # Use wrist (index 0) as origin to get translation invariance
    base_x, base_y, base_z = pts[0]

    vec: List[float] = []
    for (x, y, z) in pts:
        vec.append(x - base_x)
        vec.append(y - base_y)
        vec.append(z - base_z)

    if normalize:
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
    # Final check
    if len(vec) != EXPECTED_LENGTH:
        raise RuntimeError(f"Feature vector length {len(vec)} != expected {EXPECTED_LENGTH}")
    return vec

# Small helper: convert a list of (x,y,z) tuples to a vector (useful for unit tests)
def tuples_to_vector(tuples_xyz: List[tuple], normalize: bool = True) -> List[float]:
    if len(tuples_xyz) != NUM_LANDMARKS:
        raise ValueError(f"Expected {NUM_LANDMARKS} tuples, got {len(tuples_xyz)}")
    base_x, base_y, base_z = tuples_xyz[0]
    vec = []
    for (x, y, z) in tuples_xyz:
        vec.extend([x - base_x, y - base_y, z - base_z])
    if normalize:
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
    return vec
