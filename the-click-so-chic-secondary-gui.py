#  Copyright (C) 2025 Martin Pfeffer
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Voraussetzungen
# pip install pyautogui screeninfo

import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui
from screeninfo import get_monitors


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Clicker")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        self.running = False
        self.clicker_thread = None

        # Monitor auswählen
        self.monitors = get_monitors()
        self.monitor_info = {}
        for i, monitor in enumerate(self.monitors):
            self.monitor_info[f"Monitor {i + 1}"] = monitor

        # Debug-Ausgabe für alle Monitore
        print("Gefundene Monitore:")
        for i, m in enumerate(self.monitors):
            print(f"Monitor {i + 1}: {m.width}x{m.height} bei Position ({m.x}, {m.y})")

        self.create_widgets()
        self.update_preview()

    def show_help(self):
        help_text = """Autoclicker Hilfe:

1. Monitor auswählen: Wähle den Monitor, auf dem der Autoclicker arbeiten soll.
2. Position einstellen: Nutze die Schieberegler, um die X- und Y-Position anzupassen.
3. Klickintervall: Stelle die Zeit zwischen den Klicks ein (in Sekunden).
4. Start/Stop: Starte und stoppe den Autoclicker.

Problembehebung:
- Wenn der Klick nicht an der erwarteten Position erfolgt, überprüfe die Monitor-Konfiguration.
- Die "Aktuelle Mausposition"-Funktion kann verwendet werden, um eine genaue Position zu ermitteln.
"""
        messagebox.showinfo("Hilfe", help_text)

    def show_current_mouse_pos(self):
        # Aktuelle Mausposition anzeigen
        current_x, current_y = pyautogui.position()

        # Ermitteln, auf welchem Monitor der Cursor ist
        current_monitor = None
        monitor_name = "Unbekannt"

        for name, monitor in self.monitor_info.items():
            if (monitor.x <= current_x < monitor.x + monitor.width and
                    monitor.y <= current_y < monitor.y + monitor.height):
                current_monitor = monitor
                monitor_name = name
                break

        if current_monitor:
            # Prozentuale Position berechnen
            x_percent = round(((current_x - current_monitor.x) / current_monitor.width) * 100, 2)
            y_percent = round(((current_y - current_monitor.y) / current_monitor.height) * 100, 2)

            message = (f"Aktuelle Mausposition:\n"
                       f"Absolute Koordinaten: ({current_x}, {current_y})\n"
                       f"Auf Monitor: {monitor_name}\n"
                       f"Prozentual: {x_percent}% X, {y_percent}% Y\n\n"
                       f"Soll diese Position übernommen werden?")

            if messagebox.askyesno("Aktuelle Mausposition", message):
                # Position in die Schieberegler übernehmen
                self.x_position.set(x_percent)
                self.y_position.set(y_percent)
                self.monitor_var.set(monitor_name)
                self.update_preview()
        else:
            messagebox.showinfo("Aktuelle Mausposition",
                                f"Aktuelle Position: ({current_x}, {current_y})\n"
                                f"Konnte keinem Monitor zugeordnet werden.")

    def create_widgets(self):
        # Hauptframe
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Hilfe-Button hinzufügen
        help_button = ttk.Button(main_frame, text="?", width=2, command=self.show_help)
        help_button.grid(row=0, column=0, sticky=tk.NW, padx=0, pady=0)

        # Monitor-Auswahl
        ttk.Label(main_frame, text="Monitor auswählen:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.monitor_var = tk.StringVar()
        self.monitor_combo = ttk.Combobox(main_frame, textvariable=self.monitor_var, state="readonly")
        self.monitor_combo['values'] = list(self.monitor_info.keys())
        if self.monitor_info:
            self.monitor_combo.current(0)
        self.monitor_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.monitor_combo.bind("<<ComboboxSelected>>", self.update_preview)

        # Aktuellen Monitor anzeigen
        monitor_info_frame = ttk.LabelFrame(main_frame, text="Monitor-Info")
        monitor_info_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=5, sticky=tk.NW)
        self.monitor_info_label = ttk.Label(monitor_info_frame, text="", justify=tk.LEFT)
        self.monitor_info_label.pack(padx=5, pady=5)

        # Position X
        ttk.Label(main_frame, text="X-Position (%):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.x_position = tk.DoubleVar(value=50.0)  # Default ist die Mitte (50%)
        self.x_slider = ttk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                  variable=self.x_position, length=200)
        self.x_slider.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.x_slider.bind("<ButtonRelease-1>", self.update_preview)

        # Position Y
        ttk.Label(main_frame, text="Y-Position (%):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.y_position = tk.DoubleVar(value=50.0 + 13.0)  # Default aus deinem Code (Mitte + 13%)
        self.y_slider = ttk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                  variable=self.y_position, length=200)
        self.y_slider.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.y_slider.bind("<ButtonRelease-1>", self.update_preview)

        # Zeitintervall
        ttk.Label(main_frame, text="Klickintervall (Sekunden):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.interval_var = tk.DoubleVar(value=10.0)  # Default 10 Sekunden
        interval_frame = ttk.Frame(main_frame)
        interval_frame.grid(row=3, column=1, sticky=tk.W, pady=5)

        self.interval_slider = ttk.Scale(interval_frame, from_=0.1, to=60.0, orient=tk.HORIZONTAL,
                                         variable=self.interval_var, length=150)
        self.interval_slider.pack(side=tk.LEFT)

        self.interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=5)
        self.interval_entry.pack(side=tk.LEFT, padx=5)

        # Preview-Bereich
        ttk.Label(main_frame, text="Klick-Position Vorschau:").grid(row=4, column=0, sticky=tk.W, pady=10)
        self.preview_canvas = tk.Canvas(main_frame, width=300, height=150, bg="lightgray", bd=2, relief=tk.SUNKEN)
        self.preview_canvas.grid(row=5, column=0, columnspan=2, pady=5)

        # Koordinaten-Anzeige
        self.coord_label = ttk.Label(main_frame, text="Koordinaten: (0, 0)")
        self.coord_label.grid(row=6, column=0, columnspan=2, pady=5)

        # Start/Stop-Button
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.toggle_clicker)
        self.start_button.pack(side=tk.LEFT, padx=10)

        ttk.Button(button_frame, text="Beenden", command=self.root.destroy).pack(side=tk.LEFT, padx=10)

        # Aktuelle Mausposition anzeigen lassen
        ttk.Button(button_frame, text="Aktuelle Mausposition", command=self.show_current_mouse_pos).pack(side=tk.LEFT,
                                                                                                         padx=10)

    def update_preview(self, event=None):
        monitor_key = self.monitor_var.get()
        if not monitor_key:
            return

        monitor = self.monitor_info[monitor_key]

        # Preview-Bereich aktualisieren
        self.preview_canvas.delete("all")

        # Monitor-Rechteck zeichnen
        self.preview_canvas.create_rectangle(10, 10, 290, 140, outline="black", fill="white")

        # Monitor-Info anzeigen
        monitor_info_text = f"Monitor: {monitor.width}x{monitor.height}, Position: ({monitor.x}, {monitor.y})"
        self.preview_canvas.create_text(150, 25, text=monitor_info_text, fill="blue", font=("Arial", 8))

        # Klickposition zeichnen
        x_percent = self.x_position.get() / 100
        y_percent = self.y_position.get() / 100

        x_preview = 10 + x_percent * 280
        y_preview = 10 + y_percent * 130

        # Fadenkreuz zeichnen
        self.preview_canvas.create_line(x_preview - 10, y_preview, x_preview + 10, y_preview, fill="red", width=2)
        self.preview_canvas.create_line(x_preview, y_preview - 10, x_preview, y_preview + 10, fill="red", width=2)
        self.preview_canvas.create_oval(x_preview - 3, y_preview - 3, x_preview + 3, y_preview + 3, fill="red",
                                        outline="")

        # Echte Koordinaten berechnen
        real_x = int(monitor.x + monitor.width * x_percent)
        real_y = int(monitor.y + monitor.height * y_percent)

        self.coord_label.config(text=f"Koordinaten: ({real_x}, {real_y})")

        # Monitor-Info aktualisieren
        monitor_info_text = f"Breite: {monitor.width}px\nHöhe: {monitor.height}px\nPosition: ({monitor.x}, {monitor.y})"
        self.monitor_info_label.config(text=monitor_info_text)

    def clicker_function(self):
        monitor_key = self.monitor_var.get()
        if not monitor_key:
            messagebox.showerror("Fehler", "Kein Monitor ausgewählt!")
            self.toggle_clicker()
            return

        monitor = self.monitor_info[monitor_key]

        # Debug-Ausgabe für Monitor-Info
        print(f"Monitor Info: {monitor_key}")
        print(f"- Auflösung: {monitor.width}x{monitor.height}")
        print(f"- Position: ({monitor.x}, {monitor.y})")
        print(f"- Weitere Eigenschaften: {dir(monitor)}")

        while self.running:
            x_percent = self.x_position.get() / 100
            y_percent = self.y_position.get() / 100

            # Absolute Koordinaten für den ausgewählten Monitor berechnen
            click_x = int(monitor.x + monitor.width * x_percent)
            click_y = int(monitor.y + monitor.height * y_percent)

            try:
                # Debug-Ausgabe für den Klick
                print(f"Klicke bei {x_percent * 100}%, {y_percent * 100}% des Monitors")
                print(f"Absolute Koordinaten: ({click_x}, {click_y})")

                # Klick ausführen
                pyautogui.click(click_x, click_y)

                # Warten für das eingestellte Intervall
                interval = self.interval_var.get()
                # Kurze Intervalle für responsives Beenden
                if interval > 0.5:
                    for _ in range(int(interval * 2)):
                        if not self.running:
                            break
                        time.sleep(0.5)
                else:
                    time.sleep(interval)
            except Exception as e:
                print(f"Fehler beim Klicken: {e}")
                messagebox.showerror("Fehler beim Klicken", str(e))
                self.running = False
                break

    def toggle_clicker(self):
        if not self.running:
            # Aktuelle Position anzeigen
            monitor_key = self.monitor_var.get()
            if not monitor_key:
                messagebox.showerror("Fehler", "Kein Monitor ausgewählt!")
                return

            monitor = self.monitor_info[monitor_key]
            x_percent = self.x_position.get() / 100
            y_percent = self.y_position.get() / 100
            click_x = int(monitor.x + monitor.width * x_percent)
            click_y = int(monitor.y + monitor.height * y_percent)

            messagebox.showinfo("Autoclicker gestartet",
                                f"Der Autoclicker wird bei ({click_x}, {click_y}) auf {monitor_key}\n"
                                f"mit einem Intervall von {self.interval_var.get()} Sekunden starten.")

            self.running = True
            self.start_button.config(text="Stop")
            self.clicker_thread = threading.Thread(target=self.clicker_function)
            self.clicker_thread.daemon = True
            self.clicker_thread.start()
        else:
            self.running = False
            self.start_button.config(text="Start")


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()