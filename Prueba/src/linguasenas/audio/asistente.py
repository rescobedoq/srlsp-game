import speech_recognition as sr
import pyttsx3

class AsistenteVoz:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.motor_voz = pyttsx3.init()

    def texto_a_audio(self, comando):
        self.motor_voz.say(comando)
        self.motor_voz.runAndWait()

    def capturar_voz(self, tiempo_ruido=1.0):
        with self.microphone as fuente:
            self.recognizer.adjust_for_ambient_noise(fuente, duration=tiempo_ruido)
            audio = self.recognizer.listen(fuente)

        respuesta = {"suceso": True, "error": None, "mensaje": None}
        try:
            respuesta["mensaje"] = self.recognizer.recognize_google(audio, language="es-PE")
        except sr.RequestError:
            respuesta["suceso"] = False
            respuesta["error"] = "API no disponible"
        except sr.UnknownValueError:
            respuesta["error"] = "Habla ininteligible"
        return respuesta

    def enviar_voz(self):
        while True:
            palabra = self.capturar_voz()

            if palabra["suceso"] and palabra["mensaje"]:
                return palabra["mensaje"].lower()

            if not palabra["suceso"]:
                print(f"\nAlgo no está bien. No puedo reconocer tu micrófono o no lo tienes enchufado. <{palabra['error']}>")
                self.texto_a_audio("Algo no está bien. No puedo reconocer tu micrófono o no lo tienes enchufado.")
                exit(1)

            print("\nNo pude escucharte, ¿podrías repetirlo?")
            self.texto_a_audio("No pude escucharte, ¿podrías repetirlo?")
