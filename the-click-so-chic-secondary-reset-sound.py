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

import datetime
import random
import time
import winsound

import pyautogui
from screeninfo import get_monitors

notes = {
    'C': 261,  # C-Dur
    'D': 294,  # D-Dur
    'E': 330,  # E-Dur
    'F': 349,  # F-Dur
    'G': 392,  # G-Dur
    'A': 440,  # A-Dur
    'B': 493,  # H-Dur
    'C2': 523  # C2-Dur (eine Oktave höher)
}

melody = [
    ('E', 0.5), ('E', 0.5), ('F', 0.5), ('G', 0.5), ('G', 0.5), ('F', 0.5), ('E', 0.5), ('D', 0.5), ('C', 1.0),
    ('C', 0.5), ('D', 0.5), ('E', 0.5), ('E', 0.5), ('E', 1.0), ('D', 0.5), ('D', 0.5),
    ('E', 0.5), ('F', 0.5), ('G', 0.5), ('G', 0.5), ('F', 0.5), ('E', 0.5), ('D', 0.5), ('C', 1.0)
]


def play_sound():
    for note, duration in melody:
        # Spiele den Ton (Frequenz und Dauer)
        winsound.Beep(notes[note], int(duration * 500))  # Dauer in 1/2 Millisekunden
        time.sleep(0.1)  # Kleine Pause zwischen den Tönen


def play_beep():
    frequency = 3000  # 1000 Hz
    duration = 60  # 200 ms
    winsound.Beep(frequency, duration)


def get_monitor():
    monitors = get_monitors()
    print(f"Montior(e): {len(monitors)}")
    return monitors[0];  # AUSKOMMENTIEREN WENN ZWEITER MONITOR GEKLICKT WERDEN SOLL
    if len(monitors) > 1:
        return monitors[1]  # Der zweite Monitor (Index 1)
    else:
        print("Kein sekundärer Monitor gefunden.")
        return None


def click_middle_of_monitor():
    monitor = get_monitor()
    if monitor:
        middle_x = monitor.x + monitor.width // 2
        middle_y = (monitor.y + monitor.height // 2) + (monitor.height * 10 / 100)

        while True:
            play_sound()

            current_time = datetime.datetime.now().strftime("%H:%M:%S")

            x, y = pyautogui.position()
            pyautogui.click(middle_x, middle_y)  # Klick in der Mitte des sekundären Monitors

            play_beep()

            print(f"{current_time} - Klick({middle_x}|{middle_y}) - Monitor 2")
            time.sleep(1)  # x Sekunden warten
            pyautogui.moveTo(x, y)  # Mouse zurücksetzen
            pyautogui.click(x, y)

            sleep_time = random.randint(180, 355)
            print(f"Nächster Klick in {sleep_time} Sekunden")
            time.sleep(sleep_time)  # x Sekunden warten


if __name__ == "__main__":
    click_middle_of_monitor()
