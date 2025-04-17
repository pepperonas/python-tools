#!/usr/bin/env python3

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

import requests
import json
import time
import sys
import socket


# Farben für Terminal-Ausgabe
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_colored(text, color):
    print(f"{color}{text}{Colors.ENDC}")


def check_port_open(ip, port):
    """Prüft, ob ein bestimmter Port offen ist."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((ip, port))
    sock.close()
    return result == 0


def get_bridge_info(ip):
    """Holt detaillierte Informationen über die Bridge."""
    try:
        response = requests.get(f"http://{ip}/api/config", timeout=5)
        return response.json()
    except Exception as e:
        print_colored(f"Fehler beim Abrufen der Bridge-Informationen: {str(e)}", Colors.RED)
        return {}


def try_connect_without_button(ip, attempts=3):
    """Versucht, eine Verbindung ohne Link-Button-Druck herzustellen."""
    print_colored("\nVersuche direkte Verbindung ohne Link-Button...", Colors.BLUE)

    for i in range(attempts):
        print(f"Versuch {i + 1}/{attempts}...")
        try:
            data = {"devicetype": f"hue_emergency_tool#{i}"}
            response = requests.post(f"http://{ip}/api", json=data, timeout=5)
            result = response.json()

            if "success" in result[0]:
                return result[0]["success"]["username"]

            # Spezielle Debug-Anfrage für ältere Bridges
            data = {"devicetype": "hue_emergency_tool", "debug": True}
            response = requests.post(f"http://{ip}/api", json=data, timeout=5)
            result = response.json()

            if "success" in result[0]:
                return result[0]["success"]["username"]

            time.sleep(1)
        except Exception as e:
            print(f"Fehler: {str(e)}")
            time.sleep(1)

    return None


def try_connect_with_button(ip, attempts=5):
    """Normale Verbindungsmethode mit Link-Button."""
    print_colored("\nStandardmethode: Link-Button drücken", Colors.BLUE)
    print("Drücke jetzt den Link-Button auf deiner Hue Bridge...")

    for i in range(attempts):
        try:
            print(f"Versuch {i + 1}/{attempts}...")
            data = {"devicetype": "hue_bridge_tool"}
            response = requests.post(f"http://{ip}/api", json=data, timeout=5)
            result = response.json()

            if "success" in result[0]:
                return result[0]["success"]["username"]
            elif "error" in result[0] and result[0]["error"]["type"] == 101:
                print("Link-Button wurde nicht gedrückt oder nicht erkannt.")
            else:
                print(f"Unerwartete Antwort: {json.dumps(result)}")

            time.sleep(2)
        except Exception as e:
            print(f"Fehler: {str(e)}")
            time.sleep(1)

    return None


def try_advanced_methods(ip):
    """Versucht fortgeschrittene Methoden für problematische Bridges."""
    print_colored("\nVersuche fortgeschrittene Methoden für problematische Bridges...", Colors.BLUE)

    # Methode 1: Spezielle Header
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Hue Bridge Emergency Connect"
        }
        data = {"devicetype": "emergency_connect"}
        response = requests.post(f"http://{ip}/api", json=data, headers=headers, timeout=5)
        result = response.json()

        if "success" in result[0]:
            return result[0]["success"]["username"]
    except:
        pass

    # Methode 2: Alte API-Version
    try:
        data = {"devicetype": "hue_tool", "apiversion": "1.0"}
        response = requests.post(f"http://{ip}/api", json=data, timeout=5)
        result = response.json()

        if "success" in result[0]:
            return result[0]["success"]["username"]
    except:
        pass

    # Methode 3: Versuche eine andere Route
    try:
        data = {"devicetype": "hue_tool"}
        response = requests.post(f"http://{ip}/api/", json=data, timeout=5)  # Beachte den Schrägstrich am Ende
        result = response.json()

        if "success" in result[0]:
            return result[0]["success"]["username"]
    except:
        pass

    return None


def test_connection(ip, username):
    """Testet die Verbindung mit dem erhaltenen Username."""
    try:
        # Versuche, Informationen über die Lichter zu erhalten
        response = requests.get(f"http://{ip}/api/{username}/lights", timeout=5)
        lights = response.json()

        if isinstance(lights, dict) and not "error" in lights:
            count = len(lights)
            print_colored(f"\nVerbindung erfolgreich! Gefundene Lichter: {count}", Colors.GREEN)
            return True
        else:
            print_colored("\nVerbindung fehlgeschlagen. Ungültiger API-Key.", Colors.RED)
            return False
    except Exception as e:
        print_colored(f"\nFehler beim Testen der Verbindung: {str(e)}", Colors.RED)
        return False


def main():
    print_colored("===================================", Colors.BOLD)
    print_colored("ERWEITERTES HUE BRIDGE VERBINDUNGSTOOL", Colors.BOLD)
    print_colored("===================================", Colors.BOLD)
    print("Dieses Tool versucht mehrere Methoden, um eine Verbindung zur Hue Bridge herzustellen.")

    # Frage nach der IP-Adresse
    if len(sys.argv) > 1:
        bridge_ip = sys.argv[1]
    else:
        bridge_ip = input("Gib die IP-Adresse deiner Hue Bridge ein: ")

    # Prüfe die grundlegende Erreichbarkeit
    print_colored(f"\nPrüfe Erreichbarkeit von {bridge_ip}...", Colors.BLUE)
    if check_port_open(bridge_ip, 80):
        print_colored("✓ Bridge ist erreichbar (Port 80 ist offen)", Colors.GREEN)
    else:
        print_colored("✗ Bridge scheint nicht erreichbar zu sein (Port 80 geschlossen)", Colors.RED)
        response = input("Trotzdem fortfahren? (j/n): ")
        if response.lower() != 'j':
            sys.exit(1)

    # Hole Bridge-Informationen
    bridge_info = get_bridge_info(bridge_ip)
    if bridge_info:
        print_colored("\nBridge-Informationen:", Colors.BLUE)
        print(f"Name: {bridge_info.get('name', 'Unbekannt')}")
        print(f"MAC: {bridge_info.get('mac', 'Unbekannt')}")
        print(f"Firmware: {bridge_info.get('swversion', 'Unbekannt')}")

    # Verbindungsmethoden
    print_colored("\nStarte Verbindungsprozess...", Colors.BLUE)

    # Methode 1: Standard mit Link-Button
    username = try_connect_with_button(bridge_ip)
    if username:
        print_colored(f"\nERFOLG! API-Key erhalten: {username}", Colors.GREEN)
        test_connection(bridge_ip, username)
        return

    # Methode 2: Ohne Link-Button
    print_colored("\nStandard-Methode fehlgeschlagen. Versuche alternative Methoden...", Colors.YELLOW)
    username = try_connect_without_button(bridge_ip)
    if username:
        print_colored(f"\nERFOLG! API-Key erhalten: {username}", Colors.GREEN)
        test_connection(bridge_ip, username)
        return

    # Methode 3: Fortgeschrittene Methoden
    username = try_advanced_methods(bridge_ip)
    if username:
        print_colored(f"\nERFOLG! API-Key erhalten: {username}", Colors.GREEN)
        test_connection(bridge_ip, username)
        return

    # Wenn alle Methoden fehlschlagen
    print_colored("\nAlle Verbindungsversuche sind fehlgeschlagen.", Colors.RED)
    print_colored("\nFehlersuche-Tipps:", Colors.YELLOW)
    print("1. Prüfe, ob die Bridge richtig eingeschaltet ist (alle LEDs leuchten)")
    print("2. Starte die Bridge neu (trenne sie für 10 Sekunden vom Strom)")
    print("3. Setze die Bridge zurück (verwende die Reset-Taste auf der Unterseite)")
    print("4. Prüfe, ob ein Firmware-Update verfügbar ist (über die Hue App)")
    print("5. Verwende die offizielle Hue App, um die Bridge zu debuggen")

if __name__ == "__main__":
    main()