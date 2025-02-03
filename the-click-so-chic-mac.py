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

import pyautogui


def click_middle_screen():
    screen_width, screen_height = pyautogui.size()  # Bildschirmgröße ermitteln
    middle_x, middle_y = screen_width // 2, ((screen_height // 2) + (screen_height * 7 / 100))  # Mittelpunkt berechnen

    while True:
        pyautogui.click(middle_x, middle_y)  # Klick in der Mitte des Bildschirms
        print(f"Klick an Position: ({middle_x}, {middle_y})")
        time.sleep(10)  # 10 Sekunden warten


if __name__ == "__main__":
    click_middle_screen()
