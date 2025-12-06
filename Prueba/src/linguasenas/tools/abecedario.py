import mediapipe as mp
import cv2
import numpy as np

class ClasificadorSenia:
    def __init__(self):
        # Inicialización de MediaPipe para detección de manos
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False,
                                         max_num_hands=1,
                                         min_detection_confidence=0.7,
                                         min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils
        self.abecedario = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def procesar_mano(self, frame):
        """Procesa la imagen para detectar puntos clave de la mano."""
        image_height, image_width, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.hands.process(frame_rgb)

        if resultado.multi_hand_landmarks:
            for hand_landmarks in resultado.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                letra_detectada = self.clasificar_letra(hand_landmarks, image_width, image_height)
                return letra_detectada, frame
        
        return None, frame
    
