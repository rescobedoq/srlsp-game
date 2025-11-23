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
    
    def extraer_coordenadas(self, landmarks, frame_shape):
        """Extrae las coordenadas normalizadas de los puntos de la mano."""
        altura, ancho, _ = frame_shape
        coordenadas = [(int(p.x * ancho), int(p.y * altura)) for p in landmarks.landmark]
        return coordenadas

    def clasificar_letra(self, hand_landmarks, image_width, image_height):
        """Clasifica la letra basándose en las coordenadas."""
        # Aquí puedes añadir tu lógica para comparar distancias y asignar una letra

        def distancia_euclidiana(p1, p2):
            d = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
            return d

        # Índice (Index Finger)
        index_finger_mcp = (int(hand_landmarks.landmark[5].x * image_width), int(hand_landmarks.landmark[5].y * image_height))
        index_finger_pip = (int(hand_landmarks.landmark[6].x * image_width), int(hand_landmarks.landmark[6].y * image_height))
        index_finger_dip = (int(hand_landmarks.landmark[7].x * image_width), int(hand_landmarks.landmark[7].y * image_height))
        index_finger_tip = (int(hand_landmarks.landmark[8].x * image_width), int(hand_landmarks.landmark[8].y * image_height))
        # Pulgar (Thumb)
        thumb_cmc = (int(hand_landmarks.landmark[1].x * image_width), int(hand_landmarks.landmark[1].y * image_height))
        thumb_mcp = (int(hand_landmarks.landmark[2].x * image_width), int(hand_landmarks.landmark[2].y * image_height))
        thumb_ip = (int(hand_landmarks.landmark[3].x * image_width), int(hand_landmarks.landmark[3].y * image_height))
        thumb_tip = (int(hand_landmarks.landmark[4].x * image_width), int(hand_landmarks.landmark[4].y * image_height))
        thumb_pip = (int(hand_landmarks.landmark[2].x * image_width), int(hand_landmarks.landmark[2].y * image_height))
        # Dedo medio (Middle Finger)
        middle_finger_mcp = (int(hand_landmarks.landmark[9].x * image_width), int(hand_landmarks.landmark[9].y * image_height))
        middle_finger_pip = (int(hand_landmarks.landmark[10].x * image_width), int(hand_landmarks.landmark[10].y * image_height))
        middle_finger_dip = (int(hand_landmarks.landmark[11].x * image_width), int(hand_landmarks.landmark[11].y * image_height))
        middle_finger_tip = (int(hand_landmarks.landmark[12].x * image_width), int(hand_landmarks.landmark[12].y * image_height))
        # Anular (Ring Finger)
        ring_finger_mcp = (int(hand_landmarks.landmark[13].x * image_width), int(hand_landmarks.landmark[13].y * image_height))
        ring_finger_pip = (int(hand_landmarks.landmark[14].x * image_width), int(hand_landmarks.landmark[14].y * image_height))
        ring_finger_dip = (int(hand_landmarks.landmark[15].x * image_width), int(hand_landmarks.landmark[15].y * image_height))
        ring_finger_tip = (int(hand_landmarks.landmark[16].x * image_width), int(hand_landmarks.landmark[16].y * image_height))
        # Meñique (Pinky Finger)
        pinky_tip_mcp = (int(hand_landmarks.landmark[17].x * image_width), int(hand_landmarks.landmark[17].y * image_height))
        pinky_pip = (int(hand_landmarks.landmark[18].x * image_width), int(hand_landmarks.landmark[18].y * image_height))
        pinky_dip = (int(hand_landmarks.landmark[19].x * image_width), int(hand_landmarks.landmark[19].y * image_height))
        pinky_tip = (int(hand_landmarks.landmark[20].x * image_width), int(hand_landmarks.landmark[20].y * image_height))
        #Muñeca (wrist)
        wrist = (int(hand_landmarks.landmark[0].x * image_width), int(hand_landmarks.landmark[0].y * image_height))
                    
        ring_finger_pip2 = (int(hand_landmarks.landmark[5].x * image_width), int(hand_landmarks.landmark[5].y * image_height))
                    
        # Para fines de ejemplo, seleccionaremos una letra fija
        if abs(thumb_tip[1] - index_finger_pip[1]) <30 \
            and abs(thumb_tip[1] - middle_finger_pip[1]) < 30 and abs(thumb_tip[1] - ring_finger_pip[1]) < 30\
            and abs(thumb_tip[1] - pinky_pip[1]) < 30:
            return 'A'
                    
        elif index_finger_pip[1] > index_finger_tip[1] and pinky_pip[1] - pinky_tip[1] > 0 and \
            middle_finger_pip[1] - middle_finger_tip[1] >0 and ring_finger_pip[1] - ring_finger_tip[1] >0 and \
            middle_finger_tip[1] - ring_finger_tip[1] <0 and abs(thumb_tip[1] - ring_finger_pip2[1])<40:
            return 'B'
                        
        elif 30 < abs(index_finger_tip[1] - thumb_tip[1]) < 80 and \
            abs(index_finger_tip[0] - thumb_tip[0]) < 50 and \
            middle_finger_tip[1] > middle_finger_dip[1] and \
            ring_finger_tip[1] > ring_finger_dip[1] and \
            pinky_tip[1] > pinky_dip[1]:
            return 'C'
                    
        elif distancia_euclidiana(thumb_tip, middle_finger_tip) < 65 \
            and distancia_euclidiana(thumb_tip, ring_finger_tip) < 65 \
            and pinky_pip[1] < pinky_tip[1] \
            and middle_finger_tip[1] > middle_finger_pip[1]\
            and ring_finger_tip[1] > ring_finger_pip[1] \
            and index_finger_pip[1] > index_finger_tip[1]:       
            return 'D'   
                             
        elif index_finger_pip[1] < index_finger_tip[1] and pinky_pip[1] < pinky_tip[1]  and \
            middle_finger_pip[1] < middle_finger_tip[1] and ring_finger_pip[1] < ring_finger_tip[1] \
            and abs(index_finger_tip[1] - thumb_tip[1]) < 15 and thumb_tip[1] - index_finger_tip[1] > 0 \
            and thumb_tip[1] - middle_finger_tip[1] > 0 and thumb_tip[1] - ring_finger_tip[1] > 0:
            return 'E' 
                        
        elif  pinky_pip[1] - pinky_tip[1] > 0 and middle_finger_pip[1] - middle_finger_tip[1] > 0 and \
            ring_finger_pip[1] - ring_finger_tip[1] > 0 and index_finger_pip[1] - index_finger_tip[1] < 0 \
            and abs(thumb_pip[1] - thumb_tip[1]) > 0 and distancia_euclidiana(index_finger_tip, thumb_tip) <65:          
            return 'F'             
        # Seguimos con las demas señas

        elif 20 < abs(index_finger_tip[1] - thumb_tip[1]) < 60 and \
            10 < abs(index_finger_tip[0] - thumb_tip[0]) < 30 and \
            middle_finger_tip[1] > middle_finger_pip[1] and ring_finger_tip[1] > ring_finger_pip[1] and \
            pinky_tip[1] > pinky_pip[1]:
            return 'G' 
                    
        # Listo: H
        elif index_finger_pip[1] > index_finger_tip[1] and middle_finger_pip[1] > middle_finger_tip[1] and \
            ring_finger_pip[1] < ring_finger_tip[1] and pinky_pip[1] < pinky_tip[1] and \
            abs(index_finger_tip[1] - middle_finger_tip[1]) < 20 and \
            index_finger_tip[1] < middle_finger_tip[1] and index_finger_tip[1] < ring_finger_tip[1] and \
            index_finger_tip[1] < pinky_tip[1]:  # El índice está por encima de los demás dedos
            return 'H' 
                  
        # Listo : I
        elif pinky_tip[1] < pinky_pip[1] and index_finger_tip[1] > index_finger_dip[1] and \
            middle_finger_tip[1] > middle_finger_dip[1] and ring_finger_tip[1] > ring_finger_dip[1] and \
            thumb_tip[1] > thumb_ip[1]:
            return 'I' 
            
        # Listp:J                   
        elif pinky_tip[1] < pinky_pip[1] and index_finger_tip[1] > index_finger_dip[1] and \
            middle_finger_tip[1] > middle_finger_dip[1] and ring_finger_tip[1] > ring_finger_dip[1] and \
            thumb_tip[1] > thumb_ip[1] and \
            distancia_euclidiana(thumb_tip, index_finger_pip) < 20:  # El pulgar toca index_finger_pip:  
            return 'J'
        
        # Listo: K
        elif index_finger_tip[1] < index_finger_pip[1] and middle_finger_tip[1] < middle_finger_pip[1] and \
            ring_finger_tip[1] > ring_finger_pip[1] and pinky_tip[1] > pinky_pip[1] and \
            thumb_tip[0] < middle_finger_mcp[0] and 20< abs(index_finger_tip[1] - middle_finger_tip[1]) < 30 and\
            distancia_euclidiana(thumb_tip, index_finger_pip) < 20 and \
            index_finger_tip[1] < middle_finger_tip[1] and index_finger_tip[1] < ring_finger_tip[1] and \
            index_finger_tip[1] < pinky_tip[1]:  # El índice está por encima de los demás dedos
            
            return 'K'

        #Falta calibrar L
        #distancia_euclidiana(thumb_tip, index_finger_mcp) > 30 : Separación horizontal entre el pulgar y la base del índice
        elif distancia_euclidiana(thumb_tip, index_finger_mcp) > 30 \
            and index_finger_tip[1] < index_finger_pip[1] \
            and middle_finger_tip[1] > middle_finger_pip[1] \
            and ring_finger_tip[1] > ring_finger_pip[1] \
            and pinky_tip[1] > pinky_pip[1]:  # Meñique doblado hacia la palma
            return 'L'
        
        #Falta calibrar M
        elif wrist[1] < thumb_tip[1] and wrist[1] < index_finger_tip[1] \
            and distancia_euclidiana(thumb_tip, pinky_dip) < 20 \
            and index_finger_tip[1] < index_finger_pip[1] \
            and middle_finger_tip[1] < middle_finger_pip[1] \
            and ring_finger_tip[1] < ring_finger_pip[1] \
            and pinky_tip[1] > pinky_pip[1] \
            and abs(index_finger_tip[0] - middle_finger_tip[0]) < 15 \
            and abs(middle_finger_tip[0] - ring_finger_tip[0]) < 15:  # Separación corta entre medio y anular (eje X)
            return 'M'
        #Falta calibrar N
        elif wrist[1] < thumb_tip[1] and wrist[1] < index_finger_tip[1] \
            and distancia_euclidiana(thumb_tip, pinky_tip) < 20 \
            and distancia_euclidiana(thumb_tip, ring_finger_tip) < 20 \
            and index_finger_tip[1] < index_finger_pip[1] \
            and middle_finger_tip[1] < middle_finger_pip[1] \
            and ring_finger_tip[1] > ring_finger_pip[1] \
            and pinky_tip[1] > pinky_pip[1] \
            and abs(index_finger_tip[0] - middle_finger_tip[0]) < 15:  # Separación corta en el eje X entre índice y medio
            return 'N'
        #Falta calibrar O
        elif distancia_euclidiana(thumb_tip, index_finger_tip) < 10 \
            and distancia_euclidiana(thumb_tip, middle_finger_tip) < 10 \
            and distancia_euclidiana(thumb_tip, ring_finger_tip) < 10 \
            and distancia_euclidiana(thumb_tip, pinky_tip) < 10 \
            and index_finger_tip[1] > index_finger_pip[1] \
            and middle_finger_tip[1] > middle_finger_pip[1] \
            and ring_finger_tip[1] > ring_finger_pip[1] \
            and pinky_tip[1] > pinky_pip[1]:  # Meñique doblado hacia la palma
            return 'O'

        # and wrist[1] < pinky_tip[1] :La muñeca está por encima de todos los puntos
        # and thumb_tip[1] > index_finger_mcp[1] : El pulgar está hacia abajo
        elif wrist[1] < thumb_tip[1] and wrist[1] < index_finger_tip[1] \
            and wrist[1] < middle_finger_tip[1] and wrist[1] < ring_finger_tip[1] \
            and wrist[1] < pinky_tip[1] \
            and thumb_tip[1] > index_finger_mcp[1] \
            and index_finger_tip[1] < index_finger_mcp[1] \
            and middle_finger_tip[1] > index_finger_tip[1]:  # Medio apunta hacia abajo
            return 'P'
        
        # Falta calibrar letra Q 
        elif wrist[1] < thumb_tip[1] and wrist[1] < index_finger_tip[1] \
            and wrist[1] < middle_finger_tip[1] and wrist[1] < ring_finger_tip[1] \
            and wrist[1] < pinky_tip[1] and thumb_tip[1] < index_finger_mcp[1] \
            and index_finger_tip[1] > index_finger_pip[1] \
            and middle_finger_tip[1] > middle_finger_pip[1] \
            and ring_finger_tip[1] > ring_finger_pip[1] \
            and pinky_tip[1] > pinky_pip[1] \
            and abs(thumb_tip[0] - index_finger_tip[0]) > 10:  # Separación horizontal entre el pulgar y el índice
            return 'Q'
  
        # Falta calibrar letra R  
        elif distancia_euclidiana(index_finger_tip, middle_finger_tip) < 20 \
                and index_finger_tip[1] < index_finger_pip[1] \
                and middle_finger_tip[1] < middle_finger_pip[1] \
                and ring_finger_tip[1] > ring_finger_pip[1] \
                and pinky_tip[1] > pinky_pip[1] and thumb_tip[1] > index_finger_pip[1] \
                and distancia_euclidiana(thumb_tip, index_finger_pip) > 30:
            return 'R'
        # Letra echa con logica propia_ probar 
        elif abs(thumb_tip[0] - ring_finger_tip[0]) < 20 and abs(thumb_tip[1] - ring_finger_tip[1]) < 20 and \
            abs(index_finger_tip[0] - middle_finger_dip[0]) < 20 and \
            abs(index_finger_tip[1] - middle_finger_dip[1]) < 20 and \
            middle_finger_tip[1] < index_finger_tip[1] and \
            ring_finger_pip[1] > ring_finger_dip[1] and \
            pinky_pip[1] > pinky_dip[1] and \
            pinky_tip[1] > ring_finger_tip[1]:
            return 'R'

        # Calibrar S
        elif abs(thumb_ip[0] - index_finger_dip[0]) < 20 and abs(thumb_ip[1] - index_finger_dip[1]) < 20 and \
            abs(thumb_tip[0] - middle_finger_pip[0]) < 20 and \
            abs(thumb_tip[1] - middle_finger_pip[1]) < 20 and \
            index_finger_pip[1] > index_finger_dip[1] and \
            middle_finger_pip[1] > middle_finger_dip[1] and \
            ring_finger_pip[1] > ring_finger_dip[1] and \
            pinky_pip[1] > pinky_dip[1]:
            return 'S'

        # Calibrar T
        elif abs(thumb_tip[0] - index_finger_dip[0]) < 20 and abs(thumb_tip[1] - index_finger_dip[1]) < 20 and \
            abs(index_finger_tip[1] - index_finger_dip[1]) < 10 and \
            middle_finger_pip[1] > index_finger_pip[1] and \
            ring_finger_pip[1] > index_finger_pip[1] and \
            pinky_pip[1] > index_finger_pip[1]:
            return 'T'

       # Calibrar U
        elif abs(thumb_tip[0] - middle_finger_dip[0]) < 30 and abs(thumb_tip[1] - middle_finger_dip[1]) < 30 and \
            index_finger_pip[1] > index_finger_tip[1] and middle_finger_pip[1] < middle_finger_tip[1] and \
            ring_finger_pip[1] < ring_finger_tip[1] and pinky_pip[1] > pinky_tip[1]:
            return 'U' 
        
        # Calibrar V
        elif abs(thumb_tip[0] - ring_finger_pip[0]) < 30 and abs(thumb_tip[1] - ring_finger_pip[1]) < 30 and \
            index_finger_pip[1] > index_finger_tip[1] and \
            middle_finger_pip[1] > middle_finger_tip[1] and \
            ring_finger_pip[1] < ring_finger_tip[1] and pinky_pip[1] < pinky_tip[1] and \
            abs(index_finger_tip[0] - middle_finger_tip[0]) > 50:
            return 'V'
        # Calibrar W
        elif abs(thumb_tip[0] - pinky_tip[0]) < 30 and abs(thumb_tip[1] - pinky_tip[1]) < 30 and \
            index_finger_pip[1] > index_finger_tip[1] and \
            middle_finger_pip[1] > middle_finger_tip[1] and \
            ring_finger_pip[1] > ring_finger_tip[1] and \
            pinky_pip[1] < pinky_tip[1] and \
            abs(index_finger_tip[0] - middle_finger_tip[0]) > 50 and \
            abs(middle_finger_tip[0] - ring_finger_tip[0]) > 50:
            return 'W'
        # Calibrar X
        elif abs(thumb_tip[0] - middle_finger_dip[0]) < 30 and abs(thumb_tip[1] - middle_finger_dip[1]) < 30 and \
            index_finger_pip[1] < middle_finger_pip[1] and \
            index_finger_pip[1] < ring_finger_pip[1] and \
            index_finger_pip[1] < pinky_pip[1] and \
            index_finger_tip[1] > index_finger_pip[1] and \
            middle_finger_pip[1] < middle_finger_tip[1] and \
            ring_finger_pip[1] < ring_finger_tip[1] and \
            pinky_pip[1] < pinky_tip[1]:
            return 'X'
        
        # Calibrar letra Y
        elif abs(thumb_tip[0] - index_finger_pip[0]) > 50 and thumb_tip[1] < index_finger_pip[1] and \
            index_finger_pip[1] > middle_finger_pip[1] and \
            middle_finger_pip[1] > ring_finger_pip[1] and \
            ring_finger_pip[1] > pinky_pip[1] and \
            abs(pinky_tip[0] - ring_finger_pip[0]) > 50 and \
            pinky_tip[1] < ring_finger_pip[1]:
            return 'Y'

        # Calibrar letra Z
        elif abs(thumb_tip[0] - middle_finger_pip[0]) < 20 and \
            abs(thumb_tip[1] - middle_finger_pip[1]) < 20 and \
            index_finger_pip[1] < middle_finger_pip[1] and \
            middle_finger_pip[1] > ring_finger_pip[1] and \
            ring_finger_pip[1] > pinky_pip[1]:
            return 'Z'

        return None                             