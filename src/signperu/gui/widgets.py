#src/signperu/gui/widgets.py
# Reusable widgets for the GUI (placeholders)
def make_label(parent, text):
    try:
        import customtkinter as ctk
        return ctk.CTkLabel(parent, text=text)
    except Exception:
        class Dummy:
            def __init__(self, text):
                self.text = text
        return Dummy(text)
