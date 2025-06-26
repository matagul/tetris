"""Tetris oyun mantığı.

Pygame kullanarak temel Tetris oyunu oluşturur. Seviyeye, hıza ve renklere
göre skor toplar.
"""

import random
import pygame
from copy import deepcopy
import os
import time
import math

from . import settings
from .pieces import PIECES, Piece

class Button:
    def __init__(self, rect, text, font, color=(70, 70, 70), text_color=(255,255,255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.color = color
        self.text_color = text_color
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (200,200,200), self.rect, 2, border_radius=8)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)

class Particle:
    def __init__(self, x, y, vx, vy, color, img=None, life=30, scale=1.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.img = img
        self.life = life
        self.age = 0
        self.scale = scale
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # gravity
        self.age += 1
        self.scale *= 0.98
    def draw(self, surface):
        alpha = max(0, 255 - int(255 * (self.age / self.life)))
        if self.img:
            img = pygame.transform.rotozoom(self.img, 0, self.scale)
            img.set_alpha(alpha)
            surface.blit(img, (self.x - img.get_width()//2, self.y - img.get_height()//2))
        else:
            s = pygame.Surface((8,8), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (4,4), 4)
            surface.blit(s, (self.x-4, self.y-4))

class FallingPiece:
    def __init__(self, piece: Piece, x, y):
        self.piece = piece
        self.x = x
        self.y = y
        self.shape = deepcopy(piece.shape)
        self.color_index = piece.color_index
    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]
    def get_coords(self):
        return [(self.x + dx, self.y + dy)
                for dy, row in enumerate(self.shape)
                for dx, val in enumerate(row) if val]

class AnimatedPiece:
    def __init__(self, falling_piece):
        self.falling_piece = deepcopy(falling_piece)
        self.target_x = falling_piece.x
        self.target_y = falling_piece.y
        self.anim_x = float(falling_piece.x)
        self.anim_y = float(falling_piece.y)
        self.anim_rot = 0
        self.target_rot = 0
        self.last_shape = deepcopy(falling_piece.shape)
        self.animating = False
        self.wind_trail = []  # List of (x, y, alpha, color, rot)
        self.tail_length = 24  # longer for best graphics
    def update(self, new_x, new_y, new_shape, graphics='best'):
        dx = new_x - self.anim_x
        dy = new_y - self.anim_y
        self.anim_x += dx * 0.4
        self.anim_y += dy * 0.4
        # Animate rotation
        if new_shape != self.last_shape:
            self.target_rot += 90
            self.last_shape = deepcopy(new_shape)
        d_rot = (self.target_rot - self.anim_rot)
        self.anim_rot += d_rot * 0.3
        # Wind trail
        if graphics == 'best':
            self.tail_length = 24
        elif graphics == 'good':
            self.tail_length = 12
        else:
            self.tail_length = 0
        self.wind_trail.append((self.anim_x, self.anim_y, 180, self.falling_piece.color_index, self.anim_rot))
        if len(self.wind_trail) > self.tail_length:
            self.wind_trail.pop(0)
    def get_draw_info(self):
        return self.anim_x, self.anim_y, self.anim_rot, self.falling_piece.shape, self.falling_piece.color_index, self.wind_trail

class TetrisGame:
    def __init__(self):
        pygame.init()
        self.fullscreen = False
        self.window_size = (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Doğa Tetrisi")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 28, bold=True)
        self.score_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.state = "menu"  # menu, playing, paused, gameover
        self.grid = self.create_grid()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = 500  # ms
        self.last_fall_time = pygame.time.get_ticks()
        self.menu_buttons = self.create_menu_buttons()
        self.pause_button_rect = pygame.Rect(settings.WINDOW_WIDTH-50, 10, 40, 40)
        self.paused_buttons = self.create_paused_buttons()
        self.gameover_buttons = self.create_gameover_buttons()
        self.current_piece = None
        self.next_piece = None
        self.hold_piece = None
        self.hold_used = False
        self.spawn_new_piece()
        # Sound/music
        self.sounds = self.load_sounds()
        self.music_loaded = False
        self.play_music()
        # High scores
        self.high_scores = self.load_high_scores()
        # Animation state
        self.line_clear_anim = None  # (lines, start_time)
        self.anim_duration = 0.3
        self.lock_anim = None  # (piece, start_time)
        self.win_anim = None  # (type, start_time)
        # Background animation
        self.bg_anim_time = 0
        self.bg_image = self.load_bg_image()
        self.leaf_image = self.load_leaf_image()
        self.leaf_particles = self.create_leaves()
        # Score animation
        self.score_anim = {'value': 0, 'target': 0, 'last_update': time.time()}
        # Explosion particles
        self.explosions = []
        self.sparkle_img = self.load_img('sparkle.png')
        self.coin_img = self.load_img('coin.png')
        self.glow_img = self.load_img('glow.png')
        self.particles = []
        self.animated_piece = None
        self.menu_state = 'main'  # 'main', 'settings', 'scores'
        self.settings = dict(settings.DEFAULT_SETTINGS)
        self.mute_button_rect = pygame.Rect(10, 10, 36, 36)
        self.settings_buttons = self.create_settings_buttons()
        self.graphics_modes = ['low', 'good', 'best']
        self.leaf_timer = 0
        self.gold_shine_timer = 0
        self.berserk_ready = False
        self.berserk_anim = None
        self.last_berserk_trigger = 0
        self.player_name = "Player"
        self.name_box_active = False
        self.name_box_rect = pygame.Rect(settings.WINDOW_WIDTH//2-90, 140, 180, 40)
        self.name_box_text = ""
        self.shake_offset = [0, 0]
        self.shake_timer = 0
        self.fade_alpha = 255
        self.fade_in = True
        self.show_help = False
        self.show_quit_confirm = False
        self.is_mobile = self.detect_mobile()
        self.touch_buttons = self.create_touch_buttons() if self.is_mobile else []

    def create_menu_buttons(self):
        w, h = 180, 50
        cx = settings.WINDOW_WIDTH // 2 - w//2
        cy = settings.WINDOW_HEIGHT // 2 - 2*h
        gap = 20
        return [
            Button((cx, cy + i*(h+gap), w, h), text, self.font)
            for i, text in enumerate(["Start", "Restart", "Scores", "Settings", "How to Play", "Quit"] )
        ]
    def create_paused_buttons(self):
        w, h = 180, 50
        cx = settings.WINDOW_WIDTH // 2 - w//2
        cy = settings.WINDOW_HEIGHT // 2 - h
        gap = 20
        return [
            Button((cx, cy + i*(h+gap), w, h), text, self.font)
            for i, text in enumerate(["Resume", "Restart", "Quit"])
        ]
    def create_gameover_buttons(self):
        w, h = 180, 50
        cx = settings.WINDOW_WIDTH // 2 - w//2
        cy = settings.WINDOW_HEIGHT // 2
        gap = 20
        return [
            Button((cx, cy + i*(h+gap), w, h), text, self.font)
            for i, text in enumerate(["Restart", "Menu", "Quit"])
        ]
    def create_settings_buttons(self):
        w, h = 180, 40
        cx = settings.WINDOW_WIDTH // 2 - w//2
        cy = settings.WINDOW_HEIGHT // 2 - 2*h
        gap = 20
        return [
            Button((cx, cy + i*(h+gap), w, h), text, self.font)
            for i, text in enumerate(["Graphics: ", "Music Volume", "Effects Volume", "Mute", "Reset to Defaults", "Back"] )
        ]

    def create_grid(self):
        cols = settings.WINDOW_WIDTH // settings.BLOCK_SIZE
        rows = (settings.WINDOW_HEIGHT-60) // settings.BLOCK_SIZE
        return [[None for _ in range(cols)] for _ in range(rows)]

    def spawn_new_piece(self):
        if self.next_piece is None:
            self.current_piece = FallingPiece(random.choice(PIECES), 3, 0)
            self.next_piece = FallingPiece(random.choice(PIECES), 3, 0)
        else:
            self.current_piece = self.next_piece
            self.current_piece.x = 3
            self.current_piece.y = 0
            self.next_piece = FallingPiece(random.choice(PIECES), 3, 0)
        self.hold_used = False
        if not self.is_valid_position(self.current_piece, 0, 0):
            self.state = "gameover"
        self.animated_piece = AnimatedPiece(self.current_piece)

    def run(self):
        running = True
        self.state = 'menu'  # Always start in menu
        while running:
            self.clock.tick(settings.FPS)
            self.bg_anim_time += 1/settings.FPS
            self.gold_shine_timer += 1/settings.FPS
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.state == 'menu':
                        running = False
                    else:
                        self.show_quit_confirm = True
                if self.state == "menu":
                    self.handle_menu_event(event)
                elif self.state == "playing":
                    self.handle_game_event(event)
                elif self.state == "paused":
                    self.handle_paused_event(event)
                elif self.state == "gameover":
                    self.handle_gameover_event(event)
                if self.name_box_active:
                    self.handle_name_box_event(event)
            if self.state == "playing":
                self.update()
            self.draw()
        pygame.quit()

    def handle_menu_event(self, event):
        if self.menu_state == 'main':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.name_box_rect.collidepoint(event.pos):
                    self.name_box_active = True
                else:
                    self.name_box_active = False
                for btn in self.menu_buttons:
                    if btn.is_hovered(event.pos):
                        if btn.text == "Start":
                            self.reset_game()
                            self.state = "playing"
                            self.fade_in = True
                            self.fade_alpha = 255
                        elif btn.text == "Restart":
                            self.reset_game()
                        elif btn.text == "Scores":
                            self.menu_state = 'scores'
                        elif btn.text == "Settings":
                            self.menu_state = 'settings'
                        elif btn.text == "How to Play":
                            self.show_help = True
                        elif btn.text == "Quit":
                            self.show_quit_confirm = True
                if self.mute_button_rect.collidepoint(event.pos):
                    self.toggle_mute()
        elif self.menu_state == 'settings':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.settings_buttons):
                    if btn.is_hovered(event.pos):
                        if btn.text.startswith("Graphics"):
                            idx = self.graphics_modes.index(self.settings['graphics'])
                            self.settings['graphics'] = self.graphics_modes[(idx+1)%len(self.graphics_modes)]
                        elif btn.text == "Music Volume":
                            self.settings['music_volume'] = max(0.0, min(1.0, self.settings['music_volume']+0.1))
                            pygame.mixer.music.set_volume(0 if self.settings['mute'] else self.settings['music_volume'])
                        elif btn.text == "Effects Volume":
                            self.settings['effects_volume'] = max(0.0, min(1.0, self.settings['effects_volume']+0.1))
                            for s in self.sounds.values():
                                s.set_volume(0 if self.settings['mute'] else self.settings['effects_volume'])
                        elif btn.text == "Mute":
                            self.toggle_mute()
                        elif btn.text == "Reset to Defaults":
                            self.settings = dict(settings.DEFAULT_SETTINGS)
                            pygame.mixer.music.set_volume(self.settings['music_volume'])
                            for s in self.sounds.values():
                                s.set_volume(self.settings['effects_volume'])
                        elif btn.text == "Back":
                            self.menu_state = 'main'
        elif self.menu_state == 'scores':
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.menu_state = 'main'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            self.toggle_mute()
        if self.show_quit_confirm and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.quit_yes_rect.collidepoint(mx, my):
                pygame.quit(); exit()
            elif self.quit_no_rect.collidepoint(mx, my):
                self.show_quit_confirm = False

    def handle_name_box_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.player_name = self.name_box_text if self.name_box_text else "Player"
                self.name_box_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.name_box_text = self.name_box_text[:-1]
            elif len(self.name_box_text) < 12 and event.unicode.isprintable():
                self.name_box_text += event.unicode

    def handle_game_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.pause_button_rect.collidepoint(event.pos):
                self.state = "paused"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = "paused"
            elif event.key == pygame.K_LEFT:
                self.try_move(-1, 0)
                self.play_sound("move")
            elif event.key == pygame.K_RIGHT:
                self.try_move(1, 0)
                self.play_sound("move")
            elif event.key == pygame.K_DOWN:
                self.try_move(0, 1)
                self.play_sound("move")
            elif event.key == pygame.K_UP:
                self.try_rotate()
                self.play_sound("rotate")
            elif event.key == pygame.K_SPACE:
                self.hard_drop()
            elif event.key == pygame.K_c:
                self.hold_current_piece()
                self.play_sound("click")
            elif event.key == pygame.K_f:
                self.toggle_fullscreen()
        if event.type == pygame.VIDEORESIZE:
            # Maintain aspect ratio
            w, h = event.w, event.h
            aspect = settings.ASPECT_RATIO
            if w/h > aspect:
                h = h
                w = int(h * aspect)
            else:
                w = w
                h = int(w / aspect)
            self.window_size = (w, h)
            self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        if self.is_mobile and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.touch_buttons:
                if btn['rect'].collidepoint(event.pos):
                    if btn['action'] == 'rotate':
                        self.try_rotate()
                        self.play_sound("rotate")
                    elif btn['action'] == 'drop':
                        self.hard_drop()
                    elif btn['action'] == 'hold':
                        self.hold_current_piece()
                        self.play_sound("click")
                    elif btn['action'] == 'left':
                        self.try_move(-1, 0)
                        self.play_sound("move")
                    elif btn['action'] == 'right':
                        self.try_move(1, 0)
                        self.play_sound("move")

    def handle_paused_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.paused_buttons:
                if btn.is_hovered(event.pos):
                    if btn.text == "Resume":
                        self.state = "playing"
                    elif btn.text == "Restart":
                        self.reset_game()
                        self.state = "playing"
                    elif btn.text == "Quit":
                        pygame.quit(); exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = "playing"

    def handle_gameover_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.gameover_buttons:
                if btn.is_hovered(event.pos):
                    if btn.text == "Restart":
                        self.reset_game()
                        self.state = "playing"
                    elif btn.text == "Menu":
                        self.state = "menu"
                    elif btn.text == "Quit":
                        pygame.quit(); exit()

    def reset_game(self):
        self.grid = self.create_grid()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = 500
        self.last_fall_time = pygame.time.get_ticks()
        self.current_piece = None
        self.next_piece = None
        self.hold_piece = None
        self.hold_used = False
        self.spawn_new_piece()

    def update(self):
        now = pygame.time.get_ticks()
        self.update_leaves()
        self.update_score_anim()
        if self.line_clear_anim:
            lines, start = self.line_clear_anim
            if time.time() - start < self.anim_duration:
                return  # Wait for animation
            # Explosion effect
            for y in lines:
                for x in range(10):
                    self.explosions.append({'x': x, 'y': y, 't': 0, 'color': settings.COLORS[random.randint(0,3)]})
            self.line_clear_anim = None
        for exp in self.explosions:
            exp['t'] += 1
        self.explosions = [e for e in self.explosions if e['t'] < 20]
        if self.win_anim:
            anim_type, start = self.win_anim
            if time.time() - start > 1.0:
                self.win_anim = None
        if now - self.last_fall_time > self.fall_speed:
            self.last_fall_time = now
            if not self.try_move(0, 1):
                self.lock_piece()
                lines = self.get_full_lines()
                if lines:
                    self.line_clear_anim = (lines, time.time())
                    self.play_sound("line")
                    if len(lines) >= 2:
                        self.win_anim = ("bigwin", time.time())
                        self.play_sound("levelup")
                self.clear_lines()
                self.spawn_new_piece()
        # Level up logic
        self.level = 1 + self.lines_cleared // 10
        self.fall_speed = max(100, 500 - (self.level-1)*40)
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.age < p.life]
        # Animate piece
        graphics = self.settings.get('graphics', 'best')
        if self.animated_piece:
            self.animated_piece.update(self.current_piece.x, self.current_piece.y, self.current_piece.shape, graphics)
        # Camera shake
        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.shake_offset[0] = random.randint(-4, 4)
            self.shake_offset[1] = random.randint(-4, 4)
        else:
            self.shake_offset = [0, 0]
        # Berserk mode logic fix: only trigger once per 10 lines, after player clears 10, 20, 30... lines
        if self.lines_cleared // 10 > self.last_berserk_trigger and self.lines_cleared % 10 == 0:
            self.last_berserk_trigger = self.lines_cleared // 10
            self.berserk_ready = True
            self.berserk_anim = {'timer': 0, 'lines': [len(self.grid)-1, len(self.grid)-2]}
        if self.berserk_anim:
            self.berserk_anim['timer'] += 1
            if self.berserk_anim['timer'] == 1:
                # Remove 2 bottom lines and shift grid up
                for l in sorted(self.berserk_anim['lines']):
                    self.grid.pop()
                    self.grid.insert(0, [None for _ in range(len(self.grid[0]))])
                # Add coin/slot explosion
                for l in self.berserk_anim['lines']:
                    for x in range(len(self.grid[0])):
                        vx = random.uniform(-2,2)
                        vy = random.uniform(-4,-1)
                        img = self.coin_img if self.coin_img else None
                        self.particles.append(Particle(x*settings.BLOCK_SIZE+settings.BLOCK_SIZE//2, l*settings.BLOCK_SIZE+60+settings.BLOCK_SIZE//2, vx, vy, (255,215,0), img, 40, 1.0))
                self.play_sound("win")
            if self.berserk_anim['timer'] > 60:
                self.berserk_anim = None
                self.berserk_ready = False

    def try_move(self, dx, dy):
        if self.is_valid_position(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def try_rotate(self):
        old_shape = deepcopy(self.current_piece.shape)
        self.current_piece.rotate()
        if not self.is_valid_position(self.current_piece, 0, 0):
            # Wall kick: try shifting left or right
            if self.is_valid_position(self.current_piece, -1, 0):
                self.current_piece.x -= 1
            elif self.is_valid_position(self.current_piece, 1, 0):
                self.current_piece.x += 1
            else:
                self.current_piece.shape = old_shape
        # Animate rotation (actual shape and animation)
        if self.animated_piece:
            self.animated_piece.falling_piece.shape = deepcopy(self.current_piece.shape)
            self.animated_piece.target_rot += 90

    def hard_drop(self):
        while self.try_move(0, 1):
            pass
        self.lock_piece()
        self.clear_lines()
        self.spawn_new_piece()

    def is_valid_position(self, piece, dx, dy):
        for x, y in piece.get_coords():
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= len(self.grid[0]) or ny < 0 or ny >= len(self.grid):
                return False
            if self.grid[ny][nx] is not None:
                return False
        return True

    def lock_piece(self):
        self.lock_anim = (deepcopy(self.current_piece), time.time())
        for x, y in self.current_piece.get_coords():
            if 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]):
                self.grid[y][x] = self.current_piece.color_index
                # Add sparkle/coin particles
                for _ in range(2):
                    vx = random.uniform(-1,1)
                    vy = random.uniform(-2,-0.5)
                    img = self.coin_img if self.coin_img else None
                    self.particles.append(Particle(
                        x*settings.BLOCK_SIZE+settings.BLOCK_SIZE//2,
                        y*settings.BLOCK_SIZE+60+settings.BLOCK_SIZE//2,
                        vx, vy, settings.COLORS[self.current_piece.color_index], img, 30, 0.7))
        self.play_sound("drop")
        self.score_anim['target'] = self.score

    def clear_lines(self):
        full_lines = [i for i, row in enumerate(self.grid) if all(cell is not None for cell in row)]
        if full_lines:
            self.line_clear_anim = (full_lines, time.time())
            self.play_sound("line")
            self.shake_timer = 16  # camera shake
        new_grid = [row for row in self.grid if any(cell is None for cell in row)]
        lines_cleared = len(self.grid) - len(new_grid)
        if lines_cleared > 0:
            for _ in range(lines_cleared):
                new_grid.insert(0, [None for _ in range(len(self.grid[0]))])
            self.grid = new_grid
            self.lines_cleared += lines_cleared
            self.score += [0, 100, 300, 500, 800][lines_cleared]
            if lines_cleared >= 1:
                self.play_sound("levelup")

    def draw(self):
        self.draw_cyberpunk_background()
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "paused":
            self.draw_game()
            self.draw_paused()
        elif self.state == "gameover":
            self.draw_game()
            self.draw_gameover()
        pygame.display.flip()

    def draw_cyberpunk_background(self):
        if self.bg_image:
            bg = pygame.transform.smoothscale(self.bg_image, self.screen.get_size())
            self.screen.blit(bg, (0,0))
        else:
            self.draw_animated_background()
        # Draw animated leaves
        if self.leaf_image:
            for leaf in self.leaf_particles:
                x = int(leaf['x'])
                y = int(leaf['y'])
                scale = leaf['size']
                img = pygame.transform.rotozoom(self.leaf_image, leaf['angle']*180/math.pi, scale)
                self.screen.blit(img, (x, y))

    def draw_menu(self):
        self.draw_cyberpunk_background()
        # Top left mute button
        self.draw_mute_button()
        # Name box
        pygame.draw.rect(self.screen, (40,40,60), self.name_box_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255,255,255), self.name_box_rect, 2, border_radius=8)
        name_label = self.small_font.render("Name:", True, (255,255,255), None)
        self.screen.blit(name_label, (self.name_box_rect.x-60, self.name_box_rect.y+8))
        name_text = self.font.render(self.name_box_text if self.name_box_active else (self.player_name or "Player"), True, (255,215,0) if self.name_box_active else (255,255,255), None)
        self.screen.blit(name_text, (self.name_box_rect.x+10, self.name_box_rect.y+5))
        if self.menu_state == 'main':
            title = self.font.render("Doğa Tetrisi", True, (255,255,255), None)
            self.screen.blit(title, (settings.WINDOW_WIDTH//2 - title.get_width()//2, 80))
            for btn in self.menu_buttons:
                btn.draw(self.screen)
            # Button hover glow
            mouse = pygame.mouse.get_pos()
            for btn in self.menu_buttons:
                if btn.is_hovered(mouse):
                    glow = self.glow_img
                    if glow:
                        g = pygame.transform.smoothscale(glow, (btn.rect.width+20, btn.rect.height+20))
                        self.screen.blit(g, (btn.rect.x-10, btn.rect.y-10), special_flags=pygame.BLEND_ADD)
        elif self.menu_state == 'settings':
            title = self.font.render("Ayarlar", True, (255,255,255), None)
            self.screen.blit(title, (settings.WINDOW_WIDTH//2 - title.get_width()//2, 80))
            for i, btn in enumerate(self.settings_buttons):
                label = btn.text
                if label.startswith("Graphics"):
                    label = f"Graphics: {self.settings['graphics'].capitalize()}"
                elif label == "Music Volume":
                    label = f"Music Volume: {int(self.settings['music_volume']*100)}%"
                elif label == "Effects Volume":
                    label = f"Effects Volume: {int(self.settings['effects_volume']*100)}%"
                elif label == "Mute":
                    label = f"Mute: {'On' if self.settings['mute'] else 'Off'}"
                btn.font = self.font
                btn.text = label
                btn.draw(self.screen)
        elif self.menu_state == 'scores':
            title = self.font.render("En Yüksek Skorlar", True, (255,255,255), None)
            self.screen.blit(title, (settings.WINDOW_WIDTH//2 - title.get_width()//2, 80))
            for i, s in enumerate(self.high_scores):
                sc = self.small_font.render(f"{i+1}. {s}", True, (255,255,0 if i==0 else 200), None)
                self.screen.blit(sc, (settings.WINDOW_WIDTH//2 - sc.get_width()//2, 180 + i*32))
            back = self.small_font.render("(Tıkla veya herhangi bir tuşa bas: Geri)", True, (200,200,200), None)
            self.screen.blit(back, (settings.WINDOW_WIDTH//2 - back.get_width()//2, 400))
        # Help overlay
        if self.show_help:
            s = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
            s.fill((0,0,0,200))
            help_lines = [
                "Nasıl Oynanır:",
                "Sol/Sağ: Hareket", "Yukarı: Döndür", "Aşağı: Hızlı düşür",
                "Boşluk: Anında düşür", "ESC: Duraklat", "C: Hold", "F: Tam ekran",
                "Fare: Menü butonları", "M: Sesi aç/kapat"
            ]
            for i, line in enumerate(help_lines):
                surf = self.font.render(line, True, (255,255,255), None)
                s.blit(surf, (settings.WINDOW_WIDTH//2 - surf.get_width()//2, 120 + i*36))
            self.screen.blit(s, (0,0))
        # Quit confirmation
        if self.show_quit_confirm:
            s = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
            s.fill((0,0,0,180))
            qtext = self.font.render("Çıkmak istiyor musun?", True, (255,255,255), None)
            self.screen.blit(s, (0,0))
            self.screen.blit(qtext, (settings.WINDOW_WIDTH//2 - qtext.get_width()//2, 220))
            self.quit_yes_rect = pygame.Rect(settings.WINDOW_WIDTH//2-80, 300, 70, 40)
            self.quit_no_rect = pygame.Rect(settings.WINDOW_WIDTH//2+10, 300, 70, 40)
            pygame.draw.rect(self.screen, (80,200,80), self.quit_yes_rect, border_radius=8)
            pygame.draw.rect(self.screen, (200,80,80), self.quit_no_rect, border_radius=8)
            yes = self.font.render("Evet", True, (255,255,255), None)
            no = self.font.render("Hayır", True, (255,255,255), None)
            self.screen.blit(yes, (self.quit_yes_rect.x+10, self.quit_yes_rect.y+5))
            self.screen.blit(no, (self.quit_no_rect.x+10, self.quit_no_rect.y+5))
        # Fade-in effect
        if self.fade_in:
            self.fade_alpha = max(0, self.fade_alpha-12)
            fade = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
            fade.fill((0,0,0,self.fade_alpha))
            self.screen.blit(fade, (0,0))
            if self.fade_alpha == 0:
                self.fade_in = False

    def draw_mute_button(self, target_surface=None):
        if target_surface is None:
            target_surface = self.screen
        color = (200, 50, 50) if self.settings['mute'] else (80, 200, 80)
        pygame.draw.rect(target_surface, color, self.mute_button_rect, border_radius=8)
        pygame.draw.rect(target_surface, (255,255,255), self.mute_button_rect, 2, border_radius=8)
        # Draw mute/unmute symbol (no resource)
        cx, cy = self.mute_button_rect.center
        if self.settings['mute']:
            # Draw a speaker with a cross
            pygame.draw.polygon(target_surface, (255,255,255), [(cx-8,cy-8),(cx-8,cy+8),(cx,cy+4),(cx,cy-4)])
            pygame.draw.line(target_surface, (255,0,0), (cx-10,cy-10), (cx+10,cy+10), 3)
            pygame.draw.line(target_surface, (255,0,0), (cx-10,cy+10), (cx+10,cy-10), 3)
        else:
            # Draw a speaker with sound waves
            pygame.draw.polygon(target_surface, (255,255,255), [(cx-8,cy-8),(cx-8,cy+8),(cx,cy+4),(cx,cy-4)])
            pygame.draw.arc(target_surface, (255,255,255), (cx,cy-8,12,16), 0.5, 2.6, 2)
            pygame.draw.arc(target_surface, (255,255,255), (cx+4,cy-6,10,12), 0.5, 2.6, 1)

    def toggle_mute(self):
        self.settings['mute'] = not self.settings['mute']
        pygame.mixer.music.set_volume(0 if self.settings['mute'] else self.settings['music_volume'])
        for s in self.sounds.values():
            s.set_volume(0 if self.settings['mute'] else self.settings['effects_volume'])

    def draw_game(self):
        # Camera shake
        ox, oy = self.shake_offset
        surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.draw_grid(target_surface=surf)
        self.draw_hud(target_surface=surf)
        self.draw_piece(self.current_piece, animated=True, target_surface=surf)
        self.draw_ghost_piece(self.current_piece, target_surface=surf)
        if self.hold_piece:
            self.draw_piece_preview(self.hold_piece, 60, 120, label="Hold", target_surface=surf)
        # Pause button
        pygame.draw.rect(surf, (80,80,200), self.pause_button_rect, border_radius=8)
        pygame.draw.rect(surf, (255,255,255), self.pause_button_rect, 2, border_radius=8)
        pause_icon = self.font.render("II", True, (255,255,255))
        icon_rect = pause_icon.get_rect(center=self.pause_button_rect.center)
        surf.blit(pause_icon, icon_rect)
        # Mute button (top left)
        self.draw_mute_button(target_surface=surf)
        # Gold shine effect
        self.draw_gold_shine(target_surface=surf)
        # Berserk mode darken effect
        if self.berserk_anim:
            s = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
            s.fill((0,0,0,180))
            for l in self.berserk_anim['lines']:
                pygame.draw.rect(s, (0,0,0,0), (0, l*settings.BLOCK_SIZE+60, settings.WINDOW_WIDTH, settings.BLOCK_SIZE))
            surf.blit(s, (0,0))
        # Draw touch buttons if mobile
        if self.is_mobile:
            self.draw_touch_buttons()
        self.screen.blit(surf, (ox, oy))

    def draw_hud(self, target_surface=None):
        if target_surface is None:
            target_surface = self.screen
        # Animated gold score at center top with glow and shadow
        score_val = self.score_anim['value']
        score_surf = self.score_font.render(f"{score_val}", True, (255, 215, 0), None)
        # Shadow
        shadow = self.score_font.render(f"{score_val}", True, (0,0,0), None)
        target_surface.blit(shadow, (settings.WINDOW_WIDTH//2 - shadow.get_width()//2 + 3, 23))
        # Glow
        if self.glow_img:
            glow = pygame.transform.smoothscale(self.glow_img, (score_surf.get_width()+40, score_surf.get_height()+40))
            target_surface.blit(glow, (settings.WINDOW_WIDTH//2 - glow.get_width()//2, 0), special_flags=pygame.BLEND_ADD)
        # Score
        target_surface.blit(score_surf, (settings.WINDOW_WIDTH//2 - score_surf.get_width()//2, 20))
        # Shine effect
        shine_x = int((math.sin(self.bg_anim_time*2) + 1) * score_surf.get_width()//2)
        shine = pygame.Surface((30, score_surf.get_height()), pygame.SRCALPHA)
        pygame.draw.ellipse(shine, (255,255,255,80), shine.get_rect())
        target_surface.blit(shine, (settings.WINDOW_WIDTH//2 - score_surf.get_width()//2 + shine_x, 20))
        # Level and lines (with shadow)
        font = self.font
        level = font.render(f"Seviye: {self.level}", True, (0,255,255), None)
        lines = font.render(f"Satır: {self.lines_cleared}", True, (255,128,255), None)
        shadow2 = font.render(f"Seviye: {self.level}", True, (0,0,0), None)
        shadow3 = font.render(f"Satır: {self.lines_cleared}", True, (0,0,0), None)
        target_surface.blit(shadow2, (23, 13))
        target_surface.blit(shadow3, (settings.WINDOW_WIDTH-157, 13))
        target_surface.blit(level, (20, 10))
        target_surface.blit(lines, (settings.WINDOW_WIDTH-160, 10))
        # Next and hold previews
        self.draw_piece_preview(self.next_piece, settings.WINDOW_WIDTH-60, 120, label="Sonraki", target_surface=target_surface)
        if self.hold_piece:
            self.draw_piece_preview(self.hold_piece, 60, 120, label="Hold", target_surface=target_surface)
        # FPS counter (good/best)
        if self.settings.get('graphics','best') in ['good','best']:
            fps = int(self.clock.get_fps())
            fps_surf = self.small_font.render(f"FPS: {fps}", True, (200,255,200), None)
            target_surface.blit(fps_surf, (settings.WINDOW_WIDTH-80, settings.WINDOW_HEIGHT-30))

    def draw_piece(self, piece, animated=True, ghost=False, target_surface=None):
        if target_surface is None:
            target_surface = self.screen
        graphics = self.settings.get('graphics', 'best')
        # Use animated position/rotation for current piece
        if animated and self.animated_piece and piece == self.current_piece:
            anim_x, anim_y, anim_rot, shape, color_index, wind_trail = self.animated_piece.get_draw_info()
            # Draw wind trail (only in 'good' and 'best')
            if graphics in ['good', 'best']:
                for i, (tx, ty, alpha, cidx, trot) in enumerate(self.animated_piece.wind_trail):
                    for dy, row in enumerate(shape):
                        for dx, val in enumerate(row):
                            if val:
                                rect = pygame.Rect(
                                    int((tx+dx) * settings.BLOCK_SIZE),
                                    int((ty+dy) * settings.BLOCK_SIZE + 60),
                                    settings.BLOCK_SIZE,
                                    settings.BLOCK_SIZE,
                                )
                                color = settings.COLORS[cidx]
                                tail_color = tuple(min(255, int(x*0.7)) for x in color)
                                s = pygame.Surface((settings.BLOCK_SIZE, settings.BLOCK_SIZE), pygame.SRCALPHA)
                                pygame.draw.rect(s, (*tail_color, int(60*(i/len(self.animated_piece.wind_trail)))), (0,0,settings.BLOCK_SIZE,settings.BLOCK_SIZE), border_radius=8)
                                target_surface.blit(s, rect.topleft)
            # Draw animated piece
            for dy, row in enumerate(shape):
                for dx, val in enumerate(row):
                    if val:
                        rect = pygame.Rect(
                            int((anim_x+dx) * settings.BLOCK_SIZE),
                            int((anim_y+dy) * settings.BLOCK_SIZE + 60),
                            settings.BLOCK_SIZE,
                            settings.BLOCK_SIZE,
                        )
                        color = settings.COLORS[color_index]
                        # 3D/elemental effects for 'best' graphics
                        if graphics == 'best':
                            self.draw_elemental_effect(rect, color_index, target_surface)
                        # Glowing shadow (only in 'good' and 'best')
                        if graphics in ['good', 'best']:
                            for r in range(8, 0, -2):
                                s = pygame.Surface((settings.BLOCK_SIZE, settings.BLOCK_SIZE), pygame.SRCALPHA)
                                pygame.draw.rect(s, (*color, 20), (0,0,settings.BLOCK_SIZE,settings.BLOCK_SIZE), border_radius=r)
                                target_surface.blit(s, rect.topleft)
                        # Main block
                        pygame.draw.rect(target_surface, color, rect, border_radius=8)
                        if graphics == 'best':
                            pygame.draw.rect(target_surface, (255,255,255), rect, 2, border_radius=8)
            return
        # Fallback: static draw
        for x, y in piece.get_coords():
            if y >= 0:
                rect = pygame.Rect(
                    x * settings.BLOCK_SIZE,
                    y * settings.BLOCK_SIZE + 60,
                    settings.BLOCK_SIZE,
                    settings.BLOCK_SIZE,
                )
                color = settings.COLORS[piece.color_index]
                if ghost:
                    color = tuple(min(255, int(c*0.5)) for c in color)
                # 3D/elemental effects for 'best' graphics
                if graphics == 'best':
                    self.draw_elemental_effect(rect, piece.color_index, target_surface)
                # Glowing shadow (only in 'good' and 'best')
                if graphics in ['good', 'best']:
                    for r in range(8, 0, -2):
                        s = pygame.Surface((settings.BLOCK_SIZE, settings.BLOCK_SIZE), pygame.SRCALPHA)
                        pygame.draw.rect(s, (*color, 20), (0,0,settings.BLOCK_SIZE,settings.BLOCK_SIZE), border_radius=r)
                        target_surface.blit(s, rect.topleft)
                # Main block
                pygame.draw.rect(target_surface, color, rect, border_radius=8)
                if graphics == 'best':
                    pygame.draw.rect(target_surface, (255,255,255), rect, 2, border_radius=8)

    def draw_ghost_piece(self, piece, target_surface=None):
        if target_surface is None:
            target_surface = self.screen
        self.draw_piece(piece, animated=False, ghost=True, target_surface=target_surface)

    def draw_piece_preview(self, piece, cx, cy, label="Sonraki", target_surface=None):
        if target_surface is None:
            target_surface = self.screen
        if not piece:
            return
        shape = piece.shape
        color = settings.COLORS[piece.color_index]
        block = settings.BLOCK_SIZE // 2
        offset_x = cx - (len(shape[0])*block)//2
        offset_y = cy - (len(shape)*block)//2
        label_surf = self.small_font.render(label+":", True, (255,255,255))
        target_surface.blit(label_surf, (cx-40, cy-40))
        for dy, row in enumerate(shape):
            for dx, val in enumerate(row):
                if val:
                    rect = pygame.Rect(
                        offset_x + dx*block,
                        offset_y + dy*block,
                        block, block
                    )
                    pygame.draw.rect(target_surface, color, rect, border_radius=3)
                    pygame.draw.rect(target_surface, (255,255,255), rect, 1, border_radius=3)

    def draw_grid(self, target_surface=None):
        if target_surface is None:
            target_surface = self.screen
        graphics = self.settings.get('graphics', 'best')
        anim_lines = set(self.line_clear_anim[0]) if self.line_clear_anim else set()
        for y, row in enumerate(self.grid):
            for x, color_index in enumerate(row):
                rect = pygame.Rect(
                    x * settings.BLOCK_SIZE,
                    y * settings.BLOCK_SIZE + 60,
                    settings.BLOCK_SIZE,
                    settings.BLOCK_SIZE,
                )
                color = settings.COLORS[color_index] if color_index is not None else (50, 50, 50)
                if color_index is not None:
                    if y in anim_lines:
                        # Smooth shrink/flash
                        t = (time.time() % 1)
                        scale = 1.0 - 0.5 * abs(math.sin(t*math.pi*2))
                        s = pygame.Surface((settings.BLOCK_SIZE, settings.BLOCK_SIZE), pygame.SRCALPHA)
                        pygame.draw.rect(s, (*color, 180), (0,0,settings.BLOCK_SIZE,settings.BLOCK_SIZE), border_radius=8)
                        s = pygame.transform.smoothscale(s, (int(settings.BLOCK_SIZE*scale), int(settings.BLOCK_SIZE*scale)))
                        target_surface.blit(s, (rect.x + (settings.BLOCK_SIZE-s.get_width())//2, rect.y + (settings.BLOCK_SIZE-s.get_height())//2))
                    else:
                        # Soft shadow
                        shadow_rect = rect.move(3,3)
                        pygame.draw.rect(target_surface, (0,0,0,80), shadow_rect, border_radius=6)
                        pygame.draw.rect(target_surface, color, rect, border_radius=6)
                        pygame.draw.rect(target_surface, (255,255,255), rect, 1, border_radius=6)
                else:
                    pygame.draw.rect(target_surface, (50, 50, 50), rect, 1)
                # Draw grid lines (less visible/cooler)
                if graphics == 'best':
                    pygame.draw.rect(target_surface, (255,255,255,30), rect, 1, border_radius=8)
                elif graphics == 'good':
                    pygame.draw.rect(target_surface, (100,100,100,40), rect, 1, border_radius=8)
                else:
                    pygame.draw.rect(target_surface, (80,80,80,20), rect, 1, border_radius=8)
        # Draw explosion particles
        for exp in self.explosions:
            x = exp['x']
            y = exp['y']
            t = exp['t']
            color = exp['color']
            px = x * settings.BLOCK_SIZE + settings.BLOCK_SIZE//2 + int(8*math.sin(t))
            py = y * settings.BLOCK_SIZE + 60 + settings.BLOCK_SIZE//2 + int(8*math.cos(t))
            r = max(2, 8-t//2)
            alpha = max(0, 255-12*t)
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (r, r), r)
            target_surface.blit(s, (px-r, py-r))
        # Draw sparkle/coin particles
        for p in self.particles:
            p.draw(target_surface)

    def draw_paused(self):
        s = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,180))
        self.screen.blit(s, (0,0))
        label = self.font.render("Duraklatıldı", True, (255,255,255))
        self.screen.blit(label, (settings.WINDOW_WIDTH//2 - label.get_width()//2, 120))
        for btn in self.paused_buttons:
            btn.draw(self.screen)

    def draw_gameover(self):
        if not hasattr(self, '_score_saved'):
            self.save_high_score(self.score)
            self.play_sound("gameover")
            self._score_saved = True
        s = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,200))
        self.screen.blit(s, (0,0))
        label = self.font.render("Oyun Bitti!", True, (255,80,80))
        self.screen.blit(label, (settings.WINDOW_WIDTH//2 - label.get_width()//2, 120))
        score_label = self.font.render(f"Skor: {self.score}", True, (255,255,0))
        self.screen.blit(score_label, (settings.WINDOW_WIDTH//2 - score_label.get_width()//2, 180))
        # High scores
        hs_label = self.small_font.render("En Yüksek Skorlar:", True, (255,255,255))
        self.screen.blit(hs_label, (settings.WINDOW_WIDTH//2 - hs_label.get_width()//2, 230))
        for i, s in enumerate(self.high_scores):
            sc = self.small_font.render(f"{i+1}. {s}", True, (255,255,0) if s==self.score else (200,200,200))
            self.screen.blit(sc, (settings.WINDOW_WIDTH//2 - sc.get_width()//2, 260 + i*24))
        for btn in self.gameover_buttons:
            btn.draw(self.screen)

    def load_sounds(self):
        sounds = {}
        for name, path in [
            ("move", settings.SOUND_MOVE),
            ("rotate", settings.SOUND_ROTATE),
            ("drop", settings.SOUND_DROP),
            ("line", settings.SOUND_LINE),
            ("levelup", settings.SOUND_LEVELUP),
            ("gameover", settings.SOUND_GAMEOVER),
            ("click", settings.SOUND_CLICK),
        ]:
            if os.path.exists(path):
                sounds[name] = pygame.mixer.Sound(path)
        return sounds

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def play_music(self):
        if not self.music_loaded and os.path.exists(settings.MUSIC_BG):
            pygame.mixer.music.load(settings.MUSIC_BG)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
            self.music_loaded = True

    def load_high_scores(self):
        if not os.path.exists(settings.HIGH_SCORE_FILE):
            return []
        with open(settings.HIGH_SCORE_FILE, 'r') as f:
            return [int(line.strip()) for line in f if line.strip().isdigit()]

    def save_high_score(self, score):
        scores = self.load_high_scores() + [score]
        scores = sorted(scores, reverse=True)[:5]
        with open(settings.HIGH_SCORE_FILE, 'w') as f:
            for s in scores:
                f.write(f"{s}\n")
        self.high_scores = scores

    def get_full_lines(self):
        return [i for i, row in enumerate(self.grid) if all(cell is not None for cell in row)]

    def hold_current_piece(self):
        if self.hold_used:
            return
        if self.hold_piece is None:
            self.hold_piece = FallingPiece(self.current_piece.piece, 3, 0)
            self.spawn_new_piece()
        else:
            self.current_piece, self.hold_piece = self.hold_piece, FallingPiece(self.current_piece.piece, 3, 0)
            self.current_piece.x = 3
            self.current_piece.y = 0
        self.hold_used = True

    def load_bg_image(self):
        if os.path.exists(settings.BACKGROUND_IMAGE):
            return pygame.image.load(settings.BACKGROUND_IMAGE).convert()
        return None
    def load_leaf_image(self):
        if os.path.exists(settings.LEAF_IMAGE):
            return pygame.image.load(settings.LEAF_IMAGE).convert_alpha()
        return None
    def create_leaves(self):
        # Much rarer, smaller, more random
        leaves = []
        for _ in range(random.randint(2, 4)):
            x = random.randint(0, settings.WINDOW_WIDTH)
            y = random.randint(-settings.WINDOW_HEIGHT, 0)
            speed = random.uniform(0.2, 0.7)
            sway = random.uniform(0.5, 2.0)
            leaves.append({'x': x, 'y': y, 'speed': speed, 'sway': sway, 'angle': random.uniform(0, 2*math.pi), 'size': random.uniform(0.2, 0.5)})
        return leaves
    def update_leaves(self):
        self.leaf_timer += 1
        if self.leaf_timer > random.randint(60, 180):
            for leaf in self.leaf_particles:
                if random.random() < 0.3:
                    leaf['y'] = random.randint(-60, 0)
                    leaf['x'] = random.randint(0, settings.WINDOW_WIDTH)
            self.leaf_timer = 0
        for leaf in self.leaf_particles:
            leaf['y'] += leaf['speed']
            leaf['x'] += math.sin(self.bg_anim_time * leaf['sway'] + leaf['angle']) * 0.7
            if leaf['y'] > settings.WINDOW_HEIGHT:
                leaf['y'] = random.randint(-60, 0)
                leaf['x'] = random.randint(0, settings.WINDOW_WIDTH)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            w, h = info.current_w, info.current_h
            # Maintain aspect ratio
            aspect = settings.ASPECT_RATIO
            if w/h > aspect:
                h = h
                w = int(h * aspect)
            else:
                w = w
                h = int(w / aspect)
            self.screen = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)

    def update_score_anim(self):
        now = time.time()
        if self.score_anim['value'] < self.score_anim['target']:
            diff = self.score_anim['target'] - self.score_anim['value']
            step = max(1, int(diff * 0.2))
            self.score_anim['value'] += step
            self.score_anim['last_update'] = now
        elif self.score_anim['value'] > self.score_anim['target']:
            self.score_anim['value'] = self.score_anim['target']

    def draw_animated_background(self):
        # Vibrant animated gradient background
        t = self.bg_anim_time
        for y in range(settings.WINDOW_HEIGHT):
            color = (
                int(60 + 60 * (1 + math.sin(t + y/60)) / 2),
                int(60 + 120 * (1 + math.sin(t + y/80 + 2)) / 2),
                int(120 + 80 * (1 + math.sin(t + y/100 + 4)) / 2)
            )
            pygame.draw.line(self.screen, color, (0, y), (settings.WINDOW_WIDTH, y))
        # Optional: add floating shapes or sparkles
        for i in range(10):
            x = int((settings.WINDOW_WIDTH/10) * i + 30 * math.sin(t + i))
            y = int((settings.WINDOW_HEIGHT/10) * i + 40 * math.cos(t + i*1.5))
            r = 8 + int(4 * math.sin(t*2 + i))
            c = (
                int(180 + 60 * math.sin(t + i)),
                int(180 + 60 * math.sin(t + i*2)),
                int(180 + 60 * math.sin(t + i*3))
            )
            pygame.draw.circle(self.screen, c, (x, y), r, 0)

    def load_img(self, name):
        path = os.path.join(settings.RESOURCE_DIR, name)
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
        return None

    def draw_gold_shine(self, target_surface=None):
        if target_surface is None:
            target_surface = self.screen
        if int(self.gold_shine_timer) % 8 == 0:
            for i in range(3):
                x = random.randint(settings.WINDOW_WIDTH//2-60, settings.WINDOW_WIDTH//2+60)
                y = random.randint(10, 60)
                s = pygame.Surface((24,24), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (255,255,180,180), (0,0,24,12))
                target_surface.blit(s, (x, y), special_flags=pygame.BLEND_ADD)

    def draw_elemental_effect(self, rect, color_index, target_surface=None):
        if target_surface is None:
            target_surface = self.screen
        # 0: Fire, 1: Water, 2: Earth, 3: Air
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        if color_index == 0:  # Fire
            for i in range(6):
                pygame.draw.ellipse(s, (255, 120+i*20, 0, 60), (rect.width//2-8, rect.height//2-8-i*2, 16, 8))
            pygame.draw.ellipse(s, (255,255,0,80), (rect.width//2-8, rect.height//2-12, 16, 8))
        elif color_index == 1:  # Water
            for i in range(6):
                pygame.draw.arc(s, (0, 120+20*i, 255, 60), (2, 2+i*2, rect.width-4, rect.height-4-i*2), 0, 3.14, 2)
            pygame.draw.ellipse(s, (0,255,255,80), (rect.width//2-8, rect.height//2+4, 16, 8))
        elif color_index == 2:  # Earth
            for i in range(6):
                pygame.draw.rect(s, (139, 69+i*10, 19, 40), (4, rect.height-8-i*2, rect.width-8, 4))
            pygame.draw.ellipse(s, (80, 40, 0, 80), (rect.width//2-8, rect.height-8, 16, 8))
        elif color_index == 3:  # Air
            for i in range(6):
                pygame.draw.arc(s, (200,200,255, 40), (2, 2+i*2, rect.width-4, rect.height-4-i*2), 3.14, 6.28, 2)
            pygame.draw.ellipse(s, (255,255,255,40), (rect.width//2-8, rect.height//2-8, 16, 8))
        target_surface.blit(s, rect.topleft, special_flags=pygame.BLEND_ADD)

    def detect_mobile(self):
        # Simple heuristic: if running on Android or Kivy, or via environment
        import platform
        return 'ANDROID_ARGUMENT' in os.environ or platform.system() == 'Android'

    def create_touch_buttons(self):
        # Bottom HUD: rotate, drop, hold
        w, h = 64, 64
        y = settings.WINDOW_HEIGHT - h - 10
        gap = 20
        cx = settings.WINDOW_WIDTH // 2
        buttons = [
            {'rect': pygame.Rect(cx-w-gap, y, w, h), 'action': 'rotate'},
            {'rect': pygame.Rect(cx, y, w, h), 'action': 'drop'},
            {'rect': pygame.Rect(cx+w+gap, y, w, h), 'action': 'hold'},
        ]
        # Left/right move buttons
        my = settings.WINDOW_HEIGHT//2
        buttons.append({'rect': pygame.Rect(10, my-40, 48, 80), 'action': 'left'})
        buttons.append({'rect': pygame.Rect(settings.WINDOW_WIDTH-58, my-40, 48, 80), 'action': 'right'})
        return buttons

    def draw_touch_buttons(self):
        for btn in self.touch_buttons:
            color = (80, 80, 200) if btn['action'] in ['rotate', 'drop', 'hold'] else (80, 200, 80)
            pygame.draw.rect(self.screen, color, btn['rect'], border_radius=16)
            pygame.draw.rect(self.screen, (255,255,255), btn['rect'], 2, border_radius=16)
            icon = ''
            if btn['action'] == 'rotate':
                icon = '⟳'
            elif btn['action'] == 'drop':
                icon = '↓'
            elif btn['action'] == 'hold':
                icon = '⧗'
            elif btn['action'] == 'left':
                icon = '←'
            elif btn['action'] == 'right':
                icon = '→'
            surf = self.font.render(icon, True, (255,255,255))
            rect = surf.get_rect(center=btn['rect'].center)
            self.screen.blit(surf, rect)
