import threading
import time
import tkinter as tk

import mss
import numpy as np
import pyautogui
import pyperclip


def get_mouse_color():
    try:
        x, y = pyautogui.position()
        with mss.mss() as sct:
            monitor = sct.monitors[0]  # Hauptbildschirm
            screenshot = np.array(sct.grab(monitor))  # Screenshot als NumPy-Array

        # Sicherstellen, dass x und y im gültigen Bereich liegen
        if 0 <= x < screenshot.shape[1] and 0 <= y < screenshot.shape[0]:
            b, g, r, _ = screenshot[y, x]  # mss gibt BGR zurück
            return f'#{r:02x}{g:02x}{b:02x}'
        else:
            return "#000000"  # Falls Maus außerhalb des Screens ist
    except Exception as e:
        print(f"Error capturing screen color: {e}")
        return "#000000"  # Falls etwas schiefgeht, Standardfarbe zurückgeben


def update_color():
    while True:
        try:
            hex_color = get_mouse_color()
            text_var.set(hex_color)
            text_entry.config(bg=hex_color)  # Hintergrundfarbe setzen
        except Exception as e:
            print(f"Error: {e}")
        root.update_idletasks()
        time.sleep(0.1)  # Reduziert CPU-Last


def copy_to_clipboard():
    pyperclip.copy(text_var.get())


# GUI erstellen
root = tk.Tk()
root.title("Color Picker")
root.geometry("150x50")
root.resizable(False, False)

text_var = tk.StringVar()
text_entry = tk.Entry(root, textvariable=text_var, width=10, font=("Arial", 12))
text_entry.pack(side=tk.LEFT, padx=5, pady=5)

copy_button = tk.Button(root, text="Copy", command=copy_to_clipboard)
copy_button.pack(side=tk.RIGHT, padx=5, pady=5)

# Hintergrundprozess zum Aktualisieren der Farbe
threading.Thread(target=update_color, daemon=True).start()

root.mainloop()
