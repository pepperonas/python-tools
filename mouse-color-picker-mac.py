import sys
import time
import threading
import pyperclip
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit
from PyQt6.QtCore import Qt, QTimer
from Quartz import CGDisplayBounds, CGMainDisplayID, CGWindowListCreateImage, kCGWindowListOptionOnScreenOnly, \
    kCGNullWindowID, kCGWindowImageDefault
from AppKit import NSColorSpace, NSBitmapImageRep


def get_color_at_mouse():
    """Gibt die Farbe unter dem Mauszeiger als HEX zurück."""
    mouse_loc = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    bounds = CGDisplayBounds(CGMainDisplayID())
    image = CGWindowListCreateImage((int(mouse_loc.x), int(mouse_loc.y), 1, 1), kCGWindowListOptionOnScreenOnly,
                                    kCGNullWindowID, kCGWindowImageDefault)
    if image:
        bitmap = NSBitmapImageRep.alloc().initWithCGImage_(image)
        color = bitmap.colorAtX_y_(0, 0).colorUsingColorSpace_(NSColorSpace.sRGBColorSpace())
        if color:
            r, g, b = int(color.redComponent() * 255), int(color.greenComponent() * 255), int(
                color.blueComponent() * 255)
            return f'#{r:02X}{g:02X}{b:02X}'
    return "#000000"


class ColorPickerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.running = True
        self.color_thread = threading.Thread(target=self.update_color, daemon=True)
        self.color_thread.start()

    def init_ui(self):
        self.setWindowTitle("Color Picker")
        self.setGeometry(100, 100, 200, 50)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFixedHeight(30)

        self.copy_button = QPushButton("Copy")
        self.copy_button.setFixedHeight(30)
        self.copy_button.clicked.connect(self.copy_to_clipboard)

        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.copy_button)
        self.setLayout(self.layout)

    def update_color(self):
        """Hintergrund-Thread zur Aktualisierung der Farbe."""
        while self.running:
            color = get_color_at_mouse()
            self.text_edit.setText(color)
            time.sleep(0.1)

    def copy_to_clipboard(self):
        """Kopiert den aktuellen Farbwert in die Zwischenablage."""
        pyperclip.copy(self.text_edit.toPlainText())

    def closeEvent(self, event):
        """Stellt sicher, dass der Thread beendet wird, wenn die App geschlossen wird."""
        self.running = False
        self.color_thread.join()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorPickerApp()
    window.show()
    sys.exit(app.exec())
