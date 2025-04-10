import os
import json
import librosa
import numpy as np
from pydub import AudioSegment
import speech_recognition as speech_rec
import soundfile as sf
import tempfile


def extract_lyrics_and_pitches(audio_file):
    """
    Analysiert eine Audiodatei und extrahiert Lyrics, Tonhöhen und Zeitstempel.
    """
    print(f"Verarbeite Datei: {audio_file}")

    # Audio einlesen mit librosa
    y, sample_rate = librosa.load(audio_file)
    print(f"Audio geladen: {len(y)} Samples, {sample_rate} Hz")

    # Für Spracherkennung in wav umwandeln, falls nötig
    if audio_file.endswith('.mp3'):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_wav_name = temp_wav.name

        print("Konvertiere MP3 zu WAV...")
        audio = AudioSegment.from_mp3(audio_file)
        audio.export(temp_wav_name, format="wav")
        wav_file = temp_wav_name
        print(f"WAV-Datei erstellt: {temp_wav_name}")
    else:
        wav_file = audio_file

    # Audio in Segmente aufteilen (Stille erkennen)
    print("Erkenne Segmente...")
    intervals = librosa.effects.split(y, top_db=15)  # Niedrigerer Wert für mehr Sprachsegmente
    print(f"Anzahl erkannter Segmente: {len(intervals)}")

    lyrics = []

    # Speech Recognition initialisieren
    recognizer = speech_rec.Recognizer()

    for i, interval in enumerate(intervals):
        start_time = librosa.samples_to_time(interval[0], sr=sample_rate)
        end_time = librosa.samples_to_time(interval[1], sr=sample_rate)
        duration = end_time - start_time

        print(f"Verarbeite Segment {i + 1}/{len(intervals)}: {start_time:.2f}s - {end_time:.2f}s")

        # Segment extrahieren
        segment = y[interval[0]:interval[1]]

        # Mittlere Tonhöhe bestimmen
        if len(segment) > 0:
            try:
                pitches, magnitudes = librosa.piptrack(y=segment, sr=sample_rate)
                pitch_indices = np.argmax(magnitudes, axis=0)
                pitches_in_segment = pitches[pitch_indices, range(len(pitch_indices))]
                pitches_in_segment = pitches_in_segment[pitches_in_segment > 0]
                pitch = int(librosa.hz_to_midi(np.mean(pitches_in_segment))) if len(pitches_in_segment) > 0 else 60
            except Exception as e:
                print(f"Fehler bei Tonhöhenanalyse: {e}")
                pitch = 60
        else:
            pitch = 60

        # Nur längere Segmente verarbeiten (z.B. > 1 Sekunde)
        if duration > 1.0:
            # Segment als temporäre Datei speichern
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_segment:
                temp_segment_name = temp_segment.name

            sf.write(temp_segment_name, segment, sample_rate)

            try:
                # Verschiedene Spracherkennungsdienste probieren
                methods = [
                    ("Google", lambda src: recognizer.recognize_google(src, language="en-US")),
                    ("Sphinx", lambda src: recognizer.recognize_sphinx(src))
                ]

                recognized_text = None

                with speech_rec.AudioFile(temp_segment_name) as source:
                    audio_data = recognizer.record(source)

                    for method_name, method in methods:
                        try:
                            print(f"  Versuche Spracherkennung mit {method_name}...")
                            recognized_text = method(audio_data)
                            if recognized_text:
                                print(f"  Erkannt mit {method_name}: '{recognized_text}'")
                                break
                        except Exception as e:
                            print(f"  {method_name} fehlgeschlagen: {e}")

                if recognized_text:
                    text = recognized_text.strip()
                else:
                    print("  Keine Erkennung mit allen Methoden")
                    text = f"[Segment {i + 1}]"

            except Exception as e:
                print(f"  Fehler bei Spracherkennung: {e}")
                text = f"[Fehler: {e}]"

            os.unlink(temp_segment_name)
        else:
            print(f"  Segment zu kurz, überspringe Spracherkennung")
            text = f"[Kurzes Segment {i + 1}]"

        # Zum Ergebnis hinzufügen
        lyrics.append({
            "time": float(start_time),
            "text": text,
            "pitch": pitch,
            "duration": float(duration)
        })

    # Temporäre Dateien löschen
    if audio_file.endswith('.mp3'):
        os.unlink(temp_wav_name)

    print(f"Verarbeitung abgeschlossen. {len(lyrics)} Lyrics-Elemente erstellt.")
    return lyrics


def create_song_data(mp3_file, song_id=None):
    """
    Erzeugt das Songobjekt im gewünschten Format.
    """
    if song_id is None:
        song_id = os.path.splitext(os.path.basename(mp3_file))[0]

    # Lyrics und Pitches extrahieren
    lyrics = extract_lyrics_and_pitches(mp3_file)

    # Songobjekt erstellen
    song_data = {
        song_id: {
            "title": song_id,
            "audioUrl": mp3_file,
            "lyrics": lyrics
        }
    }

    return song_data


def process_directory(directory):
    """
    Verarbeitet alle MP3-Dateien in einem Verzeichnis.
    """
    songs = {}

    for filename in os.listdir(directory):
        if filename.endswith('.mp3'):
            file_path = os.path.join(directory, filename)
            song_id = os.path.splitext(filename)[0]
            song_data = create_song_data(file_path, song_id)
            songs.update(song_data)

    return songs


def main():
    import argparse

    parser = argparse.ArgumentParser(description='MP3 zu Karaoke-Daten konvertieren')
    parser.add_argument('--file', help='Einzelne MP3-Datei verarbeiten')
    parser.add_argument('--dir', help='Verzeichnis mit MP3-Dateien verarbeiten')
    parser.add_argument('--output', help='Ausgabedatei (JSON)', default='songs.json')
    parser.add_argument('--lyrics-only', action='store_true', help='Nur erkannte Lyrics als Text exportieren')

    args = parser.parse_args()

    songs = {}

    if args.file:
        song_data = create_song_data(args.file)
        songs.update(song_data)
    elif args.dir:
        songs = process_directory(args.dir)
    else:
        print("Entweder --file oder --dir muss angegeben werden.")
        return

    # Als JSON speichern
    with open(args.output, 'w', encoding='utf-8') as f:
        if args.lyrics_only:
            # Nur die erkannten Texte exportieren
            lyrics_text = []
            for song_id, song in songs.items():
                for line in song["lyrics"]:
                    lyrics_text.append(line["text"])

            # Als einfachen Text speichern
            with open(args.output + ".txt", 'w', encoding='utf-8') as txt_file:
                txt_file.write("\n".join(lyrics_text))
                print(f"Nur Lyrics wurden in {args.output}.txt gespeichert.")

        # Standard-JSON-Export
        json.dump({"songs": songs}, f, indent=2, ensure_ascii=False)
        print(f"Vollständige Daten wurden in {args.output} gespeichert.")


if __name__ == "__main__":
    main()
