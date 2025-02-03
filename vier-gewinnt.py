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

import numpy as np
import webbrowser
import os
import ctypes

# Function to play Rick Roll song
def play_rick_roll():
    # Open the Rick Roll video in the default web browser
    webbrowser.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    # Set system volume to maximum (Windows specific)
    os.system('nircmd.exe setsysvolume 65535')

# Function to disable closing the window
def disable_close_button():
    # Get the handle of the console window
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    # Get the menu of the console window
    hMenu = ctypes.windll.user32.GetSystemMenu(hwnd, False)
    # Disable the close button
    ctypes.windll.user32.DeleteMenu(hMenu, 0xF060, 0x00000000)

# Spielfeldgröße
ROW_COUNT = 6
COLUMN_COUNT = 7

# Erstellen des Spielfelds
def create_board():
    board = np.zeros((ROW_COUNT, COLUMN_COUNT), dtype=int)
    return board

# Spielfeld anzeigen
def print_board(board):
    print(np.flip(board, 0))

# Überprüfen, ob ein Zug gültig ist
def is_valid_location(board, col):
    return board[ROW_COUNT - 1][col] == 0

# Den nächsten freien Platz in einer Spalte finden
def get_next_open_row(board, col):
    for r in range(ROW_COUNT):
        if board[r][col] == 0:
            return r

# Überprüfen, ob ein Spieler gewonnen hat
def winning_move(board, piece):
    # Horizontale, vertikale und diagonale Überprüfungen
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True

    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True

    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True

    for c in range(COLUMN_COUNT - 3):
        for r in range(3, ROW_COUNT):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True

    return False

# Hauptspiel-Loop
def main():
    disable_close_button()  # Disable window close button at start
    board = create_board()
    game_over = False
    turn = 0

    print_board(board)

    while not game_over:
        if turn % 2 == 0:
            player = 1
            print("Spieler 1 ist am Zug (X)")
        else:
            player = 2
            print("Spieler 2 ist am Zug (O)")

        valid_move = False
        while not valid_move:
            try:
                col = int(input(f"Spieler {player}, wähle eine Spalte (0-6): "))
                if 0 <= col <= 6 and is_valid_location(board, col):
                    valid_move = True
                else:
                    print("Ungültige Spalte oder Spalte ist voll. Versuche es erneut.")
            except ValueError:
                print("Bitte gib eine Zahl zwischen 0 und 6 ein.")

        row = get_next_open_row(board, col)
        board[row][col] = player

        print_board(board)

        if winning_move(board, player):
            print(f"Spieler {player} hat gewonnen!")
            game_over = True

        turn += 1

        if np.all(board != 0):  # Wenn das Spielfeld voll ist und niemand gewonnen hat
            print("Das Spiel endet Unentschieden!")
            game_over = True

        if game_over:
            play_rick_roll()  # Play Rick Roll song when game is over

if __name__ == "__main__":
    main()