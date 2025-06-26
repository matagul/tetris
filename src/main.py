"""Tetris oyununun giris noktasi."""

from tetris.game import TetrisGame
import sys
import os


def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def main():
    oyun = TetrisGame()
    oyun.run()


if __name__ == "__main__":
    main()

RESOURCE_DIR = resource_path(os.path.join('src', 'tetris', 'resources'))
SOUND_MOVE = os.path.join(RESOURCE_DIR, 'move.wav')
# ... and so on for all resources
