#src/signperu/_main_.py
"""Entry point for signperu package.

Usage:
    python -m signperu
This will start a simple GUI (if CustomTkinter is available) or print help.
"""
import os
import sys

def main():
    try:
        from gui.main_window import MainWindow
    except Exception as e:
        print("GUI modules not available:\", e)
        print("You can still import package modules for development.")
        return

    mw = MainWindow()
    mw.run()

if __name__ == '__main__':
    main()
