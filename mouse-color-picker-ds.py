import tkinter as tk

import pyautogui
import pyperclip
from PIL import ImageGrab


class ColorPickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Color Picker")
        self.root.geometry("300x50")  # Kleine GUI

        # Textview (Label) für die Anzeige des Hex-Werts
        self.color_label = tk.Label(root, text="#FFFFFF", font=("Arial", 12), width=10)
        self.color_label.pack(side=tk.LEFT, padx=10, pady=10)

        # Button zum Kopieren des Hex-Werts
        self.copy_button = tk.Button(root, text="Copy", command=self.copy_to_clipboard)
        self.copy_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # Starte die Funktion, die die Mausbewegung überwacht
        self.update_color()

    def is_dark_color(self, hex_color):
        """Bestimme, ob die Farbe dunkel ist, basierend auf ihrer Helligkeit."""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 128

    def update_color(self):
        # Hole die aktuelle Mausposition
        x, y = pyautogui.position()

        try:
            # Hole die Farbe an der Mausposition
            color = ImageGrab.grab().load()[x, y]

            # Konvertiere den RGB-Wert in einen Hex-String
            hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])

            # Setze die Textfarbe basierend auf der Helligkeit der Hintergrundfarbe
            text_color = "white" if self.is_dark_color(hex_color) else "black"

            # Aktualisiere das Label mit dem Hex-Wert, Hintergrund und Textfarbe
            self.color_label.config(text=hex_color, bg=hex_color, fg=text_color)
        except Exception as e:
            # Fehlerbehandlung, falls die Farbe nicht erfasst werden kann
            print(f"Fehler beim Erfassen der Farbe: {e}")

        # Rufe die Funktion erneut nach 100ms auf
        self.root.after(100, self.update_color)

    def copy_to_clipboard(self):
        # Kopiere den aktuellen Hex-Wert in die Zwischenablage
        hex_value = self.color_label.cget("text")
        pyperclip.copy(hex_value)


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorPickerApp(root)
    root.mainloop()
