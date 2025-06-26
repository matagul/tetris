"""Tetris oyununun giris noktasi."""

from .tetris.game import TetrisGame
main


def main():
    oyun = TetrisGame()
    oyun.run()


if __name__ == "__main__":
    main()
