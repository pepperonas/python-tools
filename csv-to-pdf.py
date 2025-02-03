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

import pandas as pd
from fpdf import FPDF
import os

def create_pdfs_from_csv(csv_file_path, output_folder):
    # Überprüfen, ob die CSV-Datei existiert
    if not os.path.exists(csv_file_path):
        print(f"Die Datei {csv_file_path} existiert nicht.")
        return

        # Erstellen des Ausgabeverzeichnisses, falls es nicht existiert
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Zeilenweise Einlesen der CSV-Datei ohne Einschränkung auf gleiche Spaltenanzahl
        try:
            with open(csv_file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except Exception as e:
            print(f"Fehler beim Lesen der CSV-Datei: {e}")
            return

        # Iterieren über jede Zeile der Datei
        for index, line in enumerate(lines):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Entfernen von führenden/trailing Whitespaces und Hinzufügen zur PDF
        line_content = line.strip()
        values = line_content.split(';')  # Werte mit ; trennen
        for value in values:
            pdf.multi_cell(0, 10, txt=value.strip())

        # Speichern der PDF mit einem eindeutigen Namen
        pdf_file_path = os.path.join(output_folder, f"row_{index + 1}.pdf")
        pdf.output(pdf_file_path)
        print(f"PDF erstellt: {pdf_file_path}")

# Beispielaufruf der Funktion
csv_file = "beispiel.csv"  # Pfad zur CSV-Datei
output_dir = "output_pdfs"  # Ordner, in dem die PDFs gespeichert werden sollen
create_pdfs_from_csv(csv_file, output_dir)
