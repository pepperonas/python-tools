import os

import cv2
import numpy as np
import pytesseract
from PIL import ImageGrab, Image

# Pfad zu Tesseract-OCR festlegen - überprüfe diesen für dein System
# Häufige Pfade für macOS mit Homebrew
tesseract_paths = [
    '/opt/homebrew/bin/tesseract',
    '/usr/local/bin/tesseract'
]

for path in tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        print(f"Tesseract gefunden unter: {path}")
        break


def set_volume(level):
    # Level should be between 0 (mute) and 100 (max)
    if 0 <= level <= 100:
        os.system(f"osascript -e 'set volume output volume {level}'")


# TODO EINKOMMENTIEREN FÜR WINDOWS
# from comtypes import CLSCTX_ALL
# from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
# def set_volume(level):
#    # Level should be between -65.25 (mute) and 0 (max)
#    devices = AudioUtilities.GetSpeakers()
#    interface = devices.Activate(
#        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
#    volume = interface.QueryInterface(IAudioEndpointVolume)
#    volume.SetMasterVolumeLevel(level, None)


def capture_screen_region():
    # Definition des Ursprungs und der Rechteckgröße
    # TODO: SUCHE DEN ENTSPRECHENDEN BILDSCHIRM AUSSCHNITT
    origin_x, origin_y = 130, 312
    rect_width, rect_height = 100, 30

    # Berechnung der Koordinaten des Rechtecks
    x1 = origin_x
    y1 = origin_y
    x2 = origin_x + rect_width
    y2 = origin_y + rect_height

    print(f"Erfasse Bildschirmbereich: ({x1}, {y1}) bis ({x2}, {y2})")

    # Screenshot des definierten Bereichs aufnehmen
    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))

    # Konvertierung zu einem für OpenCV geeigneten Format
    screenshot_np = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    return screenshot, screenshot_cv


def perform_ocr(pil_image, cv_image):
    # Mehrere Bildverarbeitungsmethoden für bessere OCR-Ergebnisse

    # 1. Graustufenbild
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    # 2. Größere Skalierung für bessere Erkennung
    scale_factor = 2
    scaled = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    # 3. Rauschminderung
    denoised = cv2.fastNlMeansDenoising(scaled, None, 10, 7, 21)

    # 4. Kontrastverstärkung durch CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # 5. Schwellenwertverfahren
    # 5.1 Einfache Schwellenwertbildung
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 5.2 Adaptive Schwellenwertbildung
    adaptive = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Verschiedene Bilder für OCR verwenden
    images = [
        {"name": "Original PIL", "img": pil_image, "lang": "deu+eng"},
        {"name": "Original", "img": gray, "lang": "deu+eng"},
        {"name": "Binär", "img": binary, "lang": "deu+eng"},
        {"name": "Adaptiv", "img": adaptive, "lang": "deu+eng"}
    ]

    results = []
    for img_data in images:
        try:
            if isinstance(img_data["img"], Image.Image):
                text = pytesseract.image_to_string(img_data["img"], lang=img_data["lang"])
            else:
                # OpenCV-Bild in PIL Image konvertieren
                if len(img_data["img"].shape) == 2:  # Graustufenbild
                    pil_img = Image.fromarray(img_data["img"])
                else:  # Farbbild
                    pil_img = Image.fromarray(cv2.cvtColor(img_data["img"], cv2.COLOR_BGR2RGB))
                text = pytesseract.image_to_string(pil_img, lang=img_data["lang"])

            # Leerzeichen und Zeilenumbrüche entfernen
            text = text.strip()

            if text:  # Nur nicht-leere Ergebnisse speichern
                results.append({"method": img_data["name"], "text": text})

        except Exception as e:
            print(f"Fehler bei {img_data['name']}: {e}")

    # Bilder für die Visualisierung zurückgeben
    processed_images = {
        "gray": gray,
        "binary": binary,
        "adaptive": adaptive
    }

    return results, processed_images


def main():
    print("Programm zur optischen Zeichenerkennung gestartet")
    print("Ursprung bei (200, 200) mit Rechteckgröße 100x30 Pixel")
    print("Drücke 'q', um das Programm zu beenden")

    try:
        while True:
            # Bildschirmbereich erfassen
            pil_image, cv_image = capture_screen_region()

            # OCR durchführen
            results, processed_images = perform_ocr(pil_image, cv_image)

            # Erkannten Text ausgeben
            print("-" * 40)
            if results:
                for result in results:
                    print(f"Erkannter Text ({result['method']}): {result['text']}")
                    # TODO: ÄNDERE LAUTSTÄRKE
                    if 'row_2.pdf' in result['text']:
                        set_volume(50.0)
                    else:
                        set_volume(100.0)
            else:
                print("Kein Text erkannt. Versuche es mit einer besseren Textdarstellung.")

            # Visualisierung des erfassten Bereichs
            cv2.imshow("Erfasster Bereich", cv_image)

            # Verarbeitete Bilder anzeigen
            cv2.imshow("Graustufen", processed_images["gray"])
            cv2.imshow("Binär (Otsu)", processed_images["binary"])
            cv2.imshow("Adaptiv", processed_images["adaptive"])

            # Warte auf Tastendruck, 'q' zum Beenden
            if cv2.waitKey(2000) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Programm beendet")
    except Exception as e:
        print(f"Fehler im Hauptprogramm: {e}")
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        # Tesseract-Version überprüfen
        print("Tesseract Version:", pytesseract.get_tesseract_version())
        print("Verfügbare Sprachen:", pytesseract.get_languages())
        main()
    except pytesseract.pytesseract.TesseractNotFoundError:
        print("FEHLER: Tesseract ist nicht installiert oder nicht im PATH.")
        print("Bitte installiere Tesseract OCR mit:\nbrew install tesseract\nbrew install tesseract-lang")
        print("Danach starte das Programm neu.")
