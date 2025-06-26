"""Tetris oyun mantığı.

Pygame kullanarak temel Tetris oyunu oluşturur. Seviyeye, hıza ve renklere
göre skor toplar.
"""

import random
import pygame

from . import settings
from .pieces import PIECES

class TetrisGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        )
        pygame.display.set_caption("Doğa Tetrisi")
        self.clock = pygame.time.Clock()
        self.grid = self.create_grid()
        self.current_piece = self.get_new_piece()
        self.score = 0
        self.level = 1
        self.fall_speed = 500  # milisaniye cinsinden
        self.last_fall_time = pygame.time.get_ticks()

    def create_grid(self):
        cols = settings.WINDOW_WIDTH // settings.BLOCK_SIZE
        rows = settings.WINDOW_HEIGHT // settings.BLOCK_SIZE
        return [[None for _ in range(cols)] for _ in range(rows)]

    def get_new_piece(self):
        return random.choice(PIECES)

    def run(self):
        running = True
        while running:
            self.clock.tick(settings.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.update()
            self.draw()
        pygame.quit()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_fall_time > self.fall_speed:
            self.last_fall_time = now
            # Parçayı aşağı kaydırmak (basit)
            pass  # Tam tetris mantığı için geliştirilebilir

    def draw_grid(self):
        for y, row in enumerate(self.grid):
            for x, color_index in enumerate(row):
                rect = pygame.Rect(
                    x * settings.BLOCK_SIZE,
                    y * settings.BLOCK_SIZE,
                    settings.BLOCK_SIZE,
                    settings.BLOCK_SIZE,
                )
                if color_index is not None:
                    color = settings.COLORS[color_index]
                    pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.draw_grid()
        self.draw_score()
        pygame.display.flip()

    def draw_score(self):
        font = pygame.font.SysFont("Arial", 24)
        text = font.render(
            f"Skor: {self.score}  Seviye: {self.level}", True, (255, 255, 255)
        )
        self.screen.blit(text, (10, 10))
