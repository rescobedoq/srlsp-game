import time
#from asistente import AsistenteVoz
#from juego_AH import Juego_senias
#from juego_LC import JuegoLetras
#from juego_LADRILLOS import Arkanoid
import customtkinter as ctk
from PIL import Image
import queue

class VirtualAssistant:
    def __init__(self):
        self.asistente_voz = AsistenteVoz()
        self.mi_juego2 = JuegoLetras(callback=self.presentar_opciones)
        self.mi_juego = Juego_senias(callback=self.presentar_opciones)
        self.option_label = None
        self.win_choose = None
        self.console = None  # Consola embebida para mensajes

    def texto_a_audio(self, comando):
        self.asistente_voz.texto_a_audio(comando)

    def capturar_voz(self):
        return self.asistente_voz.capturar_voz()

    def enviar_voz(self):
        return self.asistente_voz.enviar_voz()

    def imprimir_mensaje(self, mensaje, leer_voz=True):
        """Imprime un mensaje en la consola embebida y el terminal, y lo lee en voz alta opcionalmente."""
        if self.console:
            self.console.insert(ctk.END, f"{mensaje}\n")
            self.console.see(ctk.END)  # Auto-scroll hacia abajo
        print(mensaje)
        if leer_voz:
            self.texto_a_audio(mensaje)  # Leer el mensaje en voz alta
    #Iniciando arkanoid...
    #Iniciando Juego Letras Caen..."

    #"Iniciando Juego Del Ahorcado..."
    def do_game(self):
        
        self.imprimir_mensaje("Iniciando Juego Del Ahorcado...")
        self.win_choose.destroy()
        juego = Juego_senias(callback=self.presentar_opciones)  # Pasar el callback
        juego.ejecutar()

    def leer_opciones(self):
        """Lee las opciones después de que la interfaz esté lista."""
        self.imprimir_mensaje("Opciones disponibles:")
        self.imprimir_mensaje(
            "1) Juego Arkanoid\n"
            "2) Juego Letras Caen\n"
            "3) Juego Del Ahorcado"
        )

    def presentar_opciones(self):
        self.win_choose = ctk.CTk()
        self.win_choose.geometry("800x600")
        self.win_choose.title("Asistente Virtual - Selección de Juegos")

        # Encabezado
        title = ctk.CTkLabel(
            self.win_choose,
            text="Seleccione un modo de juego",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(pady=20)

        # Consola para mensajes
        self.console = ctk.CTkTextbox(
            self.win_choose,
            width=700,
            height=150,
            font=("Arial", 15),
            wrap="word",
        )
        self.console.pack(pady=(10, 20))
        self.imprimir_mensaje("Bienvenido al Asistente Virtual.", leer_voz=False)

        # Crear el contenedor de las opciones (imágenes + botones)
        button_frame = ctk.CTkFrame(self.win_choose)
        button_frame.pack(pady=20, padx=10)

        # Cargar imágenes
        image_size = (200, 150)
        img_ahorcado = ctk.CTkImage(
            light_image=Image.open("images/juego_del_ahorcado.png"), size=image_size
        )

        # Opción 1: Juego Reconoce Señas

        # Opción 2: Juego Letras Caen
        
        # Opción 3: Juego del Ahorcado
        option3_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        option3_frame.grid(row=0, column=2, padx=10, pady=10)
        img_label3 = ctk.CTkLabel(option3_frame, image=img_ahorcado, text="")
        img_label3.pack(pady=5)
        juego_button = ctk.CTkButton(
            option3_frame,
            text="Juego Del Ahorcado",
            command=self.do_game,
            width=200,
        )
        juego_button.pack()

        # Leer las opciones después de que la interfaz esté lista
        self.win_choose.after(1000, self.leer_opciones)  # Esperar 1 segundo antes de leer las opciones

        self.win_choose.mainloop()
        
    def ejecutar_programa(self):
        self.presentar_opciones()


# Main para iniciar
if __name__ == "__main__":
    ctk.set_appearance_mode("System")  # Modos: System (por defecto), Dark, Light
    ctk.set_default_color_theme("blue")  # Opciones: blue, dark-blue, green
    virtual_assistant = VirtualAssistant()
    virtual_assistant.ejecutar_programa()
