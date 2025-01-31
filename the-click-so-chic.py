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
