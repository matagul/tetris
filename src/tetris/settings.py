"""Oyun ayarları.

Bu dosya, oyunun temel renkleri, pencere boyutu ve oyunla ilgili
diger sabitleri barındırır.
"""

import pygame

# Pencere boyutu
WINDOW_WIDTH = 300
WINDOW_HEIGHT = 600

# Kare boyutu
BLOCK_SIZE = 30

# Renkler (ateş, su, toprak, hava)
RED = (255, 0, 0)      # Ateş
BLUE = (0, 0, 255)     # Su
BROWN = (139, 69, 19)  # Toprak
WHITE = (255, 255, 255)  # Hava (beyaz)

COLORS = [RED, BLUE, BROWN, WHITE]

# FPS ayarı
FPS = 60
