import sys
import os
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog,
                             QSlider, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
                             QStyle, QStatusBar, QProgressBar)
from PyQt5.QtCore import Qt, QUrl, QTimer, QMimeData, pyqtSignal, QObject
from PyQt5.QtGui import QPalette, QColor, QDragEnterEvent, QDropEvent
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

# Matplotlib-Optimierungen
import matplotlib
matplotlib.rcParams['agg.path.chunksize'] = 10000  # Für schnelleres Rendering
matplotlib.use('Qt5Agg')  # Explizit Qt5Agg-Backend verwenden
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import librosa
import soundfile as sf
import numpy as np


class WorkerSignals(QObject):
    """Signale für Worker-Thread"""
    finished = pyqtSignal(object)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)


class AudioCutter(QMainWindow):
    def __init__(self):
        super().__init__()

        # Hauptfarbe für die GUI
        self.main_color = "#2C2E3B"
        self.accent_color = "#4F5379"
        self.text_color = "#FFFFFF"

        # Audio-Eigenschaften
        self.audio_file = None
        self.waveform = None
        self.display_waveform = None  # Downsample-Version für Anzeige
        self.sr = None
        self.display_sr = None
        self.duration = 0
        self.start_pos = 0
        self.end_pos = 0
        self.dragging_start = False
        self.dragging_end = False
        self.marker_size = 10

        # Player für die gesamte Datei
        self.player = QMediaPlayer()
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)

        # Player für den Ausschnitt
        self.preview_player = QMediaPlayer()
        self.temp_preview_file = None

        # Performance-Einstellungen
        self.canvas_update_timer = QTimer()
        self.canvas_update_timer.setSingleShot(True)
        self.canvas_update_timer.timeout.connect(self.delayed_canvas_update)

        # Worker-Signale
        self.worker_signals = WorkerSignals()
        self.worker_signals.finished.connect(self.on_audio_loaded)
        self.worker_signals.progress.connect(self.update_progress)
        self.worker_signals.error.connect(self.on_load_error)

        # Drag & Drop aktivieren
        self.setAcceptDrops(True)

        self.init_ui()
        self.set_style()

    def init_ui(self):
        self.setWindowTitle("Audio Cutter")
        self.setGeometry(100, 100, 800, 500)

        # Hauptwidget und Layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Waveform-Anzeige
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        plt.tight_layout()  # Kompaktere Grafik für bessere Performance
        self.canvas = FigureCanvas(self.fig)
        # Canvas-Optimierungen
        plt.rcParams['path.simplify'] = True
        plt.rcParams['path.simplify_threshold'] = 1.0  # Statt setRenderHint
        self.ax.set_facecolor(self.main_color)
        self.fig.patch.set_facecolor(self.main_color)
        self.canvas.setStyleSheet(f"background-color: {self.main_color};")

        # Fortschrittsbalken für Ladevorgang
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)

        # Buttons
        button_layout = QHBoxLayout()

        self.load_btn = QPushButton("Audio laden")
        self.load_btn.clicked.connect(self.load_audio)

        self.play_btn = QPushButton(self.style().standardIcon(QStyle.SP_MediaPlay), "")
        self.play_btn.clicked.connect(self.play_pause)
        self.play_btn.setEnabled(False)

        # Abspielen des Ausschnitts
        self.play_selection_btn = QPushButton("Ausschnitt abspielen")
        self.play_selection_btn.clicked.connect(self.play_selection)
        self.play_selection_btn.setEnabled(False)

        self.set_start_btn = QPushButton("Start setzen")
        self.set_start_btn.clicked.connect(self.set_start)
        self.set_start_btn.setEnabled(False)

        self.set_end_btn = QPushButton("Ende setzen")
        self.set_end_btn.clicked.connect(self.set_end)
        self.set_end_btn.setEnabled(False)

        # Start verschieben mit Pfeiltasten
        start_adjust_layout = QHBoxLayout()
        self.start_left_btn = QPushButton("◀")
        self.start_left_btn.clicked.connect(lambda: self.adjust_marker("start", -0.1))
        self.start_left_btn.setEnabled(False)

        self.start_right_btn = QPushButton("▶")
        self.start_right_btn.clicked.connect(lambda: self.adjust_marker("start", 0.1))
        self.start_right_btn.setEnabled(False)

        start_adjust_layout.addWidget(QLabel("Start:"))
        start_adjust_layout.addWidget(self.start_left_btn)
        start_adjust_layout.addWidget(self.start_right_btn)

        # Ende verschieben mit Pfeiltasten
        end_adjust_layout = QHBoxLayout()
        self.end_left_btn = QPushButton("◀")
        self.end_left_btn.clicked.connect(lambda: self.adjust_marker("end", -0.1))
        self.end_left_btn.setEnabled(False)

        self.end_right_btn = QPushButton("▶")
        self.end_right_btn.clicked.connect(lambda: self.adjust_marker("end", 0.1))
        self.end_right_btn.setEnabled(False)

        end_adjust_layout.addWidget(QLabel("Ende:"))
        end_adjust_layout.addWidget(self.end_left_btn)
        end_adjust_layout.addWidget(self.end_right_btn)

        adjustment_layout = QHBoxLayout()
        adjustment_layout.addLayout(start_adjust_layout)
        adjustment_layout.addLayout(end_adjust_layout)

        self.cut_btn = QPushButton("Ausschneiden")
        self.cut_btn.clicked.connect(self.cut_audio)
        self.cut_btn.setEnabled(False)

        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.play_btn)
        button_layout.addWidget(self.play_selection_btn)
        button_layout.addWidget(self.set_start_btn)
        button_layout.addWidget(self.set_end_btn)
        button_layout.addWidget(self.cut_btn)

        # Zeitleiste
        time_layout = QHBoxLayout()

        self.current_time = QLabel("00:00")
        self.total_time = QLabel("00:00")

        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 0)
        self.time_slider.sliderMoved.connect(self.slider_moved)

        time_layout.addWidget(self.current_time)
        time_layout.addWidget(self.time_slider)
        time_layout.addWidget(self.total_time)

        # Markierungsanzeige
        marker_layout = QHBoxLayout()
        self.start_label = QLabel("Start: 00:00")
        self.end_label = QLabel("Ende: 00:00")
        marker_layout.addWidget(self.start_label)
        marker_layout.addWidget(self.end_label)

        # Status-Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Alles zum Hauptlayout hinzufügen
        main_layout.addWidget(self.canvas)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(time_layout)
        main_layout.addLayout(marker_layout)
        main_layout.addLayout(adjustment_layout)  # Hinzufügen der Anpassungsbuttons
        main_layout.addLayout(button_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Canvas-Events für Klick und Drag verbinden
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        self.canvas.mpl_connect('button_release_event', self.on_canvas_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_canvas_drag)

    def set_style(self):
        # Dark mode style
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {self.main_color};
                color: {self.text_color};
            }}
            QPushButton {{
                background-color: {self.accent_color};
                color: {self.text_color};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #5E638C;
            }}
            QPushButton:disabled {{
                background-color: #3A3C4E;
                color: #8C8C8C;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #999999;
                height: 8px;
                background: {self.accent_color};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #D0D0D0;
                border: 1px solid #5c5c5c;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }}
            QLabel {{
                color: {self.text_color};
            }}
            QProgressBar {{
                border: 1px solid #5E638C;
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: #5E638C;
                width: 10px;
                margin: 0.5px;
            }}
        """)

    def load_audio(self, filepath=None):
        if not filepath:
            options = QFileDialog.Options()
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Audio laden", "", "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a);;All Files (*)",
                options=options
            )

        if filepath:
            # UI vorbereiten
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.statusBar.showMessage("Lade Audio...")
            self.load_btn.setEnabled(False)
            QApplication.processEvents()

            # Funktion in separatem Thread ausführen
            threading.Thread(target=self._load_audio_thread, args=(filepath,)).start()

    def _load_audio_thread(self, filepath):
        try:
            # Bibliotheken importieren
            import librosa
            import soundfile as sf

            # Wir brauchen zusätzliche Libraries für m4a-Unterstützung
            try:
                # Audio mit reduzierter Abtastrate laden für bessere Performance
                if filepath.lower().endswith('.m4a'):
                    import pydub
                    from io import BytesIO

                    self.worker_signals.progress.emit(20, "Konvertiere M4A...")

                    # M4A mit pydub laden und zu WAV konvertieren
                    audio = pydub.AudioSegment.from_file(filepath, format="m4a")

                    # In einen RAM-Buffer exportieren
                    buffer = BytesIO()
                    audio.export(buffer, format="wav")
                    buffer.seek(0)

                    # Librosa kann aus Binary Data laden
                    self.worker_signals.progress.emit(30, "M4A zu WAV konvertiert, lade Audio...")
                    data, sr = sf.read(buffer)
                    buffer.close()

                    # Mono konvertieren falls nötig
                    if len(data.shape) > 1 and data.shape[1] > 1:
                        waveform = np.mean(data, axis=1)
                    else:
                        waveform = data

                    # Auf 22050 Hz resampling falls nötig
                    if sr != 22050:
                        self.worker_signals.progress.emit(40, "Resampling...")
                        waveform = librosa.resample(waveform, orig_sr=sr, target_sr=22050)
                        sr = 22050
                else:
                    # Standard-Methode für andere Formate
                    self.worker_signals.progress.emit(10, "Lade Audio-Datei...")
                    waveform, sr = librosa.load(filepath, sr=22050, mono=True)
            except Exception as e:
                # Fehler beim Laden des M4A, versuche Standardmethode
                self.worker_signals.progress.emit(10, f"M4A-Fehler, versuche Standardmethode: {str(e)}")
                waveform, sr = librosa.load(filepath, sr=22050, mono=True)

            self.worker_signals.progress.emit(50, "Verarbeite Audio...")

            # Downsampling für die Anzeige (reduziert Datenpunkte)
            if len(waveform) > 100000:
                factor = len(waveform) // 100000 + 1
                display_waveform = waveform[::factor]
                display_sr = sr // factor
            else:
                display_waveform = waveform
                display_sr = sr

            duration = librosa.get_duration(y=waveform, sr=sr)

            self.worker_signals.progress.emit(90, "Bereite Anzeige vor...")

            # Ergebnisse zurückgeben
            result = {
                'waveform': waveform,
                'sr': sr,
                'display_waveform': display_waveform,
                'display_sr': display_sr,
                'duration': duration,
                'filepath': filepath
            }

            self.worker_signals.finished.emit(result)

        except Exception as e:
            self.worker_signals.error.emit(str(e))

    def update_progress(self, value, message):
        """Aktualisiert die Fortschrittsanzeige"""
        self.progress_bar.setValue(value)
        self.statusBar.showMessage(message)
        QApplication.processEvents()

    def on_audio_loaded(self, result):
        """Wird aufgerufen, wenn das Audio erfolgreich geladen wurde"""
        # Daten übernehmen
        self.waveform = result['waveform']
        self.sr = result['sr']
        self.display_waveform = result['display_waveform']
        self.display_sr = result['display_sr']
        self.duration = result['duration']
        self.audio_file = result['filepath']

        # Datei für QMediaPlayer laden
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.audio_file)))

        # UI-Elemente aktualisieren
        self.play_btn.setEnabled(True)
        self.set_start_btn.setEnabled(True)
        self.set_end_btn.setEnabled(True)

        # Marker-Anpassung aktivieren
        self.start_left_btn.setEnabled(True)
        self.start_right_btn.setEnabled(True)
        self.end_left_btn.setEnabled(True)
        self.end_right_btn.setEnabled(True)

        # Waveform anzeigen
        self.plot_waveform()

        # Ende Standard auf Länge der Datei setzen
        self.start_pos = 0
        self.end_pos = self.duration
        self.update_marker_labels()
        self.update_cut_button()

        # UI zurücksetzen
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
        self.statusBar.showMessage(f"Audio geladen: {os.path.basename(self.audio_file)}")

    def on_load_error(self, error_message):
        """Wird aufgerufen, wenn ein Fehler beim Laden auftritt"""
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
        self.statusBar.showMessage(f"Fehler beim Laden: {error_message}")

    # Drag & Drop Implementierung
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            # Prüfen, ob die URL eine Audio-Datei ist
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                file_ext = os.path.splitext(url.toLocalFile())[1].lower()
                if file_ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']:
                    event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            self.load_audio(file_path)

    def plot_waveform(self):
        self.ax.clear()

        # Benutze die downsample-Version der Waveform
        time = np.linspace(0, self.duration, len(self.display_waveform))

        # Optimierung: Nur jeden n-ten Punkt zeichnen für große Dateien
        plot_step = max(1, len(time) // 3000)  # Max. 3000 Punkte anzeigen
        self.ax.plot(time[::plot_step], self.display_waveform[::plot_step], color='#5E638C')

        # Achsen anpassen
        self.ax.set_xlabel('Zeit (s)', color=self.text_color)
        self.ax.set_ylabel('Amplitude', color=self.text_color)

        # Gitterlinien
        self.ax.grid(True, color='#4A4C5C', linestyle='--', alpha=0.6)

        # Achsenfarbe anpassen
        self.ax.tick_params(axis='x', colors=self.text_color)
        self.ax.tick_params(axis='y', colors=self.text_color)
        self.ax.spines['bottom'].set_color(self.text_color)
        self.ax.spines['top'].set_color(self.text_color)
        self.ax.spines['left'].set_color(self.text_color)
        self.ax.spines['right'].set_color(self.text_color)

        self.canvas.draw()

    def plot_waveform_with_markers(self):
        self.plot_waveform()

        # Markierungen für Start- und Endposition hinzufügen
        if self.start_pos < self.end_pos:
            # Bereich markieren
            self.ax.axvspan(self.start_pos, self.end_pos, alpha=0.3, color='#6A8CFF')

            # Vertikale Linien für Start und Ende
            self.ax.axvline(x=self.start_pos, color='#4CAF50', linestyle='-', alpha=0.8)
            self.ax.axvline(x=self.end_pos, color='#FF5252', linestyle='-', alpha=0.8)

            # Marker für Start und Ende (für Drag & Drop auf der Wellenform)
            self.ax.plot(self.start_pos, 0, 'o', color='#4CAF50', markersize=self.marker_size)
            self.ax.plot(self.end_pos, 0, 'o', color='#FF5252', markersize=self.marker_size)

            self.canvas.draw()

    def position_changed(self, position):
        # Position in Sekunden
        pos_seconds = position / 1000

        # Zeit-Label aktualisieren
        self.current_time.setText(self.format_time(pos_seconds))

        # Slider aktualisieren, ohne erneuten Aufruf auszulösen
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(position)
        self.time_slider.blockSignals(False)

    def duration_changed(self, duration):
        # Slider-Bereich aktualisieren
        self.time_slider.setRange(0, duration)

        # Zeit-Label aktualisieren
        self.total_time.setText(self.format_time(duration / 1000))

    def slider_moved(self, position):
        # Wenn der Slider vom Benutzer bewegt wird
        self.player.setPosition(position)

    def play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.player.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def set_start(self):
        # Aktuelle Position als Startposition setzen
        self.start_pos = self.player.position() / 1000

        # Sicherstellen, dass Start nicht nach Ende liegt
        if self.start_pos > self.end_pos:
            self.start_pos = self.end_pos

        self.update_marker_labels()
        self.update_cut_button()

        # Waveform mit Markierung aktualisieren
        self.plot_waveform_with_markers()

    def set_end(self):
        # Aktuelle Position als Endposition setzen
        self.end_pos = self.player.position() / 1000

        # Sicherstellen, dass Ende nicht vor Start liegt
        if self.end_pos < self.start_pos:
            self.end_pos = self.start_pos

        self.update_marker_labels()
        self.update_cut_button()

        # Waveform mit Markierung aktualisieren
        self.plot_waveform_with_markers()

    def update_marker_labels(self):
        self.start_label.setText(f"Start: {self.format_time(self.start_pos)}")
        self.end_label.setText(f"Ende: {self.format_time(self.end_pos)}")

    def update_cut_button(self):
        # Cut-Button und Preview-Button aktivieren, wenn ein gültiger Bereich ausgewählt wurde
        valid_selection = self.start_pos < self.end_pos
        self.cut_btn.setEnabled(valid_selection)
        self.play_selection_btn.setEnabled(valid_selection)

    def cut_audio(self):
        if self.audio_file and self.start_pos < self.end_pos:
            options = QFileDialog.Options()
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Ausschnitt speichern", "", "WAV Files (*.wav);;All Files (*)",
                options=options
            )

            if save_path:
                try:
                    # Ausschnitt erstellen und speichern
                    self.save_audio_cut(save_path)
                    self.statusBar.showMessage(f"Ausschnitt gespeichert: {os.path.basename(save_path)}")

                except Exception as e:
                    self.statusBar.showMessage(f"Fehler beim Speichern: {str(e)}")

    def save_audio_cut(self, save_path, is_temp=False):
        """Speichert den ausgewählten Ausschnitt"""
        # Start- und Endposition in Samples umrechnen
        start_sample = int(self.start_pos * self.sr)
        end_sample = int(self.end_pos * self.sr)

        # Ausschnitt erstellen
        audio_cut = self.waveform[start_sample:end_sample]

        # Als Datei speichern
        sf.write(save_path, audio_cut, self.sr)

        return save_path

    def play_selection(self):
        """Spielt den aktuell ausgewählten Bereich ab"""
        if self.audio_file and self.start_pos < self.end_pos:
            try:
                # Temporärer Dateiname im gleichen Verzeichnis wie die Originaldatei
                temp_dir = os.path.dirname(self.audio_file)
                temp_filename = os.path.join(temp_dir, "_temp_preview.wav")

                # Wenn bereits eine temporäre Datei existiert, löschen
                if self.temp_preview_file and os.path.exists(self.temp_preview_file):
                    try:
                        # Stoppen des Players falls er läuft
                        self.preview_player.stop()
                        os.remove(self.temp_preview_file)
                    except:
                        pass

                # Ausschnitt in temporäre Datei speichern
                self.temp_preview_file = self.save_audio_cut(temp_filename, is_temp=True)

                # Abspielen
                self.preview_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.temp_preview_file)))
                self.preview_player.play()

                self.statusBar.showMessage("Ausschnitt wird abgespielt...")

            except Exception as e:
                self.statusBar.showMessage(f"Fehler beim Abspielen des Ausschnitts: {str(e)}")

    def adjust_marker(self, marker_type, delta):
        """Passt die Start- oder Endposition um delta Sekunden an"""
        if marker_type == "start":
            self.start_pos += delta
            # Sicherstellen, dass Start nicht negativ oder nach Ende liegt
            self.start_pos = max(0, min(self.start_pos, self.end_pos - 0.01))
        else:  # end
            self.end_pos += delta
            # Sicherstellen, dass Ende nicht vor Start oder nach Dateiende liegt
            self.end_pos = max(self.start_pos + 0.01, min(self.end_pos, self.duration))

        self.update_marker_labels()
        self.update_cut_button()

        # Verzögertes Update des Canvas
        if not self.canvas_update_timer.isActive():
            self.canvas_update_timer.start(50)

    def format_time(self, seconds):
        """Formatiert Sekunden in MM:SS Format"""
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes:02d}:{seconds:02d}"

    def delayed_canvas_update(self):
        """Verzögertes Update der Canvas-Anzeige für bessere Performance"""
        self.plot_waveform_with_markers()

    # Funktionen für die Interaktion mit der Wellenform-Anzeige
    def on_canvas_click(self, event):
        """Wird aufgerufen, wenn auf die Wellenform geklickt wird"""
        if event.xdata is None or not self.waveform is not None:
            return

        # Prüfen, ob auf einen der Marker geklickt wurde
        if abs(event.xdata - self.start_pos) < 0.2:
            self.dragging_start = True
        elif abs(event.xdata - self.end_pos) < 0.2:
            self.dragging_end = True
        else:
            # An die Position springen
            pos_ms = int(event.xdata * 1000)
            self.player.setPosition(pos_ms)

    def on_canvas_release(self, event):
        """Wird aufgerufen, wenn die Maustaste losgelassen wird"""
        self.dragging_start = False
        self.dragging_end = False

    def on_canvas_drag(self, event):
        """Wird aufgerufen, wenn die Maus mit gedrückter Taste bewegt wird"""
        if event.xdata is None or not self.waveform is not None:
            return

        if self.dragging_start:
            # Start-Marker verschieben
            self.start_pos = max(0, min(event.xdata, self.end_pos - 0.01))
            self.update_marker_labels()
            self.update_cut_button()

            # Canvas-Update verzögern für bessere Performance
            if not self.canvas_update_timer.isActive():
                self.canvas_update_timer.start(50)  # 50ms Verzögerung

        elif self.dragging_end:
            # End-Marker verschieben
            self.end_pos = max(self.start_pos + 0.01, min(event.xdata, self.duration))
            self.update_marker_labels()
            self.update_cut_button()

            # Canvas-Update verzögern für bessere Performance
            if not self.canvas_update_timer.isActive():
                self.canvas_update_timer.start(50)  # 50ms Verzögerung


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AudioCutter()
    window.show()
    sys.exit(app.exec_())