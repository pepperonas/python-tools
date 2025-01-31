import sys
import threading
import time

import Quartz
import pyperclip
from AppKit import NSColorSpace, NSBitmapImageRep
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from Quartz import CGWindowListCreateImage, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, CGRectMake


class ColorUpdater(QObject):
    color_updated = pyqtSignal(str)


def get_color_at_mouse():
    event = Quartz.CGEventCreate(None)
    mouse_loc = Quartz.CGEventGetLocation(event)
    rect = CGRectMake(mouse_loc.x, mouse_loc.y, 1, 1)
    image = CGWindowListCreateImage(
        rect,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
        0  # kCGWindowImageDefault = 0
    )
    if image:
        bitmap = NSBitmapImageRep.alloc().initWithCGImage_(image)
        color = bitmap.colorAtX_y_(0, 0).colorUsingColorSpace_(NSColorSpace.sRGBColorSpace())
        if color:
            r = int(color.redComponent() * 255)
            g = int(color.greenComponent() * 255)
            b = int(color.blueComponent() * 255)
            return f'#{r:02X}{g:02X}{b:02X}'
    return "#000000"


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

        self.info_label = QLabel("CTRL to copy")
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
        if event.key() == Qt.Key.Key_Control:
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
