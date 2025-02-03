import sys
import threading
import time

import pyautogui
import pyperclip
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PIL import ImageGrab


class ColorUpdater(QObject):
    color_updated = pyqtSignal(str)


def get_color_at_mouse():
    x, y = pyautogui.position()
    image = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
    color = image.getpixel((0, 0))
    return f'#{color[0]:02X}{color[1]:02X}{color[2]:02X}'


class ColorPickerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.running = True
        self.current_color = "#000000"
        self.color_updater = ColorUpdater()
        self.color_updater.color_updated.connect(self.update_ui)
        self.color_thread = threading.Thread(target=self.update_color, daemon=True)
        self.color_thread.start()

    def init_ui(self):
        self.setWindowTitle("Color Picker")
        self.setGeometry(100, 100, 200, 60)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.layout = QVBoxLayout()

        self.color_label = QLabel("#000000")
        self.color_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_label.setStyleSheet("background-color: #000000; color: white; font-size: 16px;")

        self.info_label = QLabel("Alt to copy")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 12px;")

        self.layout.addWidget(self.color_label)
        self.layout.addWidget(self.info_label)
        self.setLayout(self.layout)

    def update_color(self):
        while self.running:
            color = get_color_at_mouse()
            if color != self.current_color:
                self.current_color = color
                self.color_updater.color_updated.emit(color)
            time.sleep(0.05)

    def update_ui(self, color):
        self.color_label.setText(color)
        luminance = (0.299 * int(color[1:3], 16) + 0.587 * int(color[3:5], 16) + 0.114 * int(color[5:7], 16))
        text_color = "black" if luminance > 186 else "white"
        self.color_label.setStyleSheet(f"background-color: {color}; color: {text_color}; font-size: 16px;")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Alt:
            pyperclip.copy(self.current_color)

    def closeEvent(self, event):
        self.running = False
        self.color_thread.join()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorPickerApp()
    window.show()
    sys.exit(app.exec())