"""Oyun ayarları.

Bu dosya, oyunun temel renkleri, pencere boyutu ve oyunla ilgili
diger sabitleri barındırır.
"""

import pygame
import os
import sys

def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

# Aspect ratio constants
ASPECT_RATIO = 1/2  # width/height (classic Tetris is 10x20 blocks)
DEFAULT_WIDTH = 400
DEFAULT_HEIGHT = 800

# Pencere boyutu
WINDOW_WIDTH = DEFAULT_WIDTH
WINDOW_HEIGHT = DEFAULT_HEIGHT

# Kare boyutu (auto-calculated)
BLOCK_SIZE = WINDOW_WIDTH // 10

# Renkler (ateş, su, toprak, hava)
RED = (255, 0, 0)      # Ateş
BLUE = (0, 0, 255)     # Su
BROWN = (139, 69, 19)  # Toprak
WHITE = (255, 255, 255)  # Hava (beyaz)

COLORS = [RED, BLUE, BROWN, WHITE]

# FPS ayarı
FPS = 60

# Resource paths (use resource_path for PyInstaller compatibility)
RESOURCE_DIR = resource_path(os.path.join('src', 'tetris', 'resources'))
SOUND_MOVE = os.path.join(RESOURCE_DIR, 'move.wav')
SOUND_ROTATE = os.path.join(RESOURCE_DIR, 'rotate.wav')
SOUND_DROP = os.path.join(RESOURCE_DIR, 'drop.wav')
SOUND_LINE = os.path.join(RESOURCE_DIR, 'line.wav')
SOUND_LEVELUP = os.path.join(RESOURCE_DIR, 'levelup.wav')
SOUND_GAMEOVER = os.path.join(RESOURCE_DIR, 'gameover.wav')
SOUND_CLICK = os.path.join(RESOURCE_DIR, 'click.wav')
SOUND_WIN = os.path.join(RESOURCE_DIR, 'win.wav')
SOUND_COIN = os.path.join(RESOURCE_DIR, 'coin.wav')
MUSIC_BG = os.path.join(RESOURCE_DIR, 'bgm.mp3')

# High score file (write to user home for EXE compatibility)
USERDATA_DIR = os.path.join(os.path.expanduser('~'), '.tetris_userdata')
if not os.path.exists(USERDATA_DIR):
    os.makedirs(USERDATA_DIR, exist_ok=True)
HIGH_SCORE_FILE = os.path.join(USERDATA_DIR, 'highscores.txt')

# Background image (cyberpunk chill world)
BACKGROUND_IMAGE = os.path.join(RESOURCE_DIR, 'cyberpunk_bg.jpg')
LEAF_IMAGE = os.path.join(RESOURCE_DIR, 'pink_leaf.png')

# Default settings
DEFAULT_SETTINGS = {
    'music_volume': 0.5,
    'effects_volume': 0.7,
    'mute': False,
    'graphics': 'best',  # 'low', 'good', 'best'
}
