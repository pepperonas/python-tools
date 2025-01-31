# Voraussetzungen
# pip install pyautogui screeninfo

import time

import pyautogui
from screeninfo import get_monitors


def get_monitor():
    monitors = get_monitors()
    print(f"Montiore: ({len(monitors)})")
    return monitors[0];  # AUSKOMMENTIEREN WENN ZWEITER MONITOR GEKLICKT WERDEN SOLL
    if len(monitors) > 1:
        return monitors[1]  # Der zweite Monitor (Index 1)
    else:
        print("Kein sekundärer Monitor gefunden.")
        return None


def click_middle_of_secondary_monitor():
    monitor = get_monitor()
    if monitor:
        middle_x = monitor.x + monitor.width // 2
        middle_y = (monitor.y + monitor.height // 2) + (monitor.height * 13 / 100)

        while True:
            pyautogui.click(middle_x, middle_y)  # Klick in der Mitte des sekundären Monitors
            print(f"Klick an Position: ({middle_x}, {middle_y}) auf Monitor 2")
            time.sleep(10)  # x Sekunden warten


if __name__ == "__main__":
    click_middle_of_secondary_monitor()
