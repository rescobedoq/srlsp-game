# src/signperu/test/quick_test_debug.py
import time
import cv2
from signperu.core.detector import DetectorWrapper

def main(duration=20, cam_src=0):
    det = DetectorWrapper()
    cap = cv2.VideoCapture(cam_src, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0)
    if not cap.isOpened():
        print("ERROR: no se pudo abrir la cámara.")
        return
    t0 = time.time()
    print("Prueba rápida con debug. Mira la cámara...")
    while time.time() - t0 < duration:
        ret, frame = cap.read()
        if not ret:
            continue
        letra, annotated, coords = det.detect_from_frame(frame)
        if letra:
            print("Señal detectada:", letra)
        if coords:
            print("Landmarks:", coords[:5], "... total:", len(coords))
        # mostramos feed anotado por si hay landmarks
        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        cv2.imshow("Debug annotated (q para salir)", annotated_rgb)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    print("Fin prueba.")
    
if __name__ == "__main__":
    main()
