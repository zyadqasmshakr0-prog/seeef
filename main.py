import pygame
import sys
import math
import time
import os

from world import World
from enemies import Enemy
from stage_layout import StageLayout
from main_menu import MainMenu, load_settings, fix_text, get_arabic_font
from game_paths import asset_path
from progression import load_progress, save_progress, add_coins, complete_stage
from display_utils import present

IS_ANDROID = (sys.platform == "android" or "ANDROID_ARGUMENT" in os.environ)

# امنع SDL2 من تحويل اللمسة إلى نقرة ماوس اصطناعية؛ نعالج كل إصبع
# من أحداث FINGER بشكل مستقل، وهذا ضروري للّمس المتعدد على Android.
if IS_ANDROID:
    os.environ["SDL_TOUCH_MOUSE_EVENTS"] = "0"
    os.environ["SDL_MOUSE_TOUCH_EVENTS"] = "0"

pygame.init()

# مساحة لعب منطقية ثابتة حتى تبقى إحداثيات المراحل ومحرر الأزرار متوافقة.
# على Android نطلب من SDL2 تحجيم هذه المساحة إلى دقة الشاشة الفعلية.
WIDTH = 1280
HEIGHT = 720
FPS = 60

if IS_ANDROID:
    try:
        # دع SDL2 يتولى تحجيم المساحة المنطقية بدلاً من تحجيم صورة الشاشة
        # كاملة داخل Python في كل إطار؛ هذا أخف كثيراً على الهواتف.
        pygame.display_surface = pygame.display.set_mode(
            (WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED
        )
        screen = pygame.display_surface
    except (pygame.error, TypeError):
        pygame.display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        screen = pygame.Surface((WIDTH, HEIGHT)).convert()

else:
    pygame.display_surface = pygame.display.set_mode((WIDTH, HEIGHT))
    screen = pygame.display_surface

pygame.display.set_caption("SEF - The Adventurer")
clock = pygame.time.Clock()
game_progress = load_progress()

SKY = (110, 180, 235)
GROUND = (70, 55, 40)
GRASS = (60, 150, 70)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (210, 50, 50)
BLUE = (50, 100, 220)
GOLD = (240, 190, 40)
PURPLE = (150, 70, 220)
CYAN = (70, 220, 255)

WORLD_WIDTH = 35000
GROUND_Y = 570

camera_x = 0
camera_y = 0
pruned_world_x = 0
last_prune_camera_x = 0

class PlayerAnimator:
    _sheet_cache = {}
    _frame_cache = {}
    _flip_cache = {}
    _scaled_cache = {}

    def __init__(self, filepath, start_frame, frame_count, speed=0.2, loop=True):
        self.frames = []
        self.frame_keys = []
        self.current_frame = 0
        self.speed = speed
        self.finished = False
        self.loop = loop
        cache_path = os.path.abspath(filepath)

        try:
            sheet = self._sheet_cache.get(cache_path)
            if sheet is None:
                sheet = pygame.image.load(filepath).convert_alpha()
                self._sheet_cache[cache_path] = sheet

            frame_w, frame_h = 50, 37
            columns = max(1, sheet.get_width() // frame_w)
            for i in range(frame_count):
                index = start_frame + i
                key = (cache_path, index)
                frame = self._frame_cache.get(key)
                if frame is None:
                    col = index % columns
                    row = index // columns
                    rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
                    frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                    frame.blit(sheet, (0, 0), rect)
                    self._frame_cache[key] = frame
                self.frames.append(frame)
                self.frame_keys.append(key)
        except Exception as e:
            print(f"تعذر تحميل حركة الشخصية من {filepath}: {e}")

    def update(self):
        if not self.frames:
            return
        self.current_frame += self.speed
        if self.current_frame >= len(self.frames):
            if self.loop:
                self.current_frame = 0
            else:
                self.current_frame = len(self.frames) - 1
            self.finished = True
        else:
            self.finished = False

    def get_current_image(self, facing_right=True):
        if not self.frames:
            return None
        index = max(0, min(len(self.frames) - 1, int(self.current_frame)))
        img = self.frames[index]
        if not facing_right:
            key = self.frame_keys[index]
            flipped = self._flip_cache.get(key)
            if flipped is None:
                flipped = pygame.transform.flip(img, True, False)
                self._flip_cache[key] = flipped
            img = flipped
        return img

class Player:
    def __init__(self):
        self.x = 300
        self.y = GROUND_Y - 100
        self.width = 55
        self.height = 100
        self.vel_x = 0
        self.vel_y = 0
        self.knockback_x = 0  
        self.speed = 6
        self.jump_power = -15
        self.gravity = 0.7
        self.on_ground = False
        self.current_floor_y = GROUND_Y
        self.max_jumps = 3 + min(3, int(game_progress.get("extra_jump_level", 0)))
        self.jumps_left = self.max_jumps
        self.facing = 1
        self.max_health = 100
        self.health = 100
        self.lives = 3
        self.max_lives = 3
        self.shield_timer = 0
        self.shield_cooldown = 0
        self.legendary_cooldown = 0
        self.last_safe_pos = (300, GROUND_Y - 100)
        self.state = "idle"
        self.crouching = False
        
        sheet_path = asset_path("adventurer-v1.5-Sheet.png")
        self.animations = {
            "idle": PlayerAnimator(sheet_path, start_frame=0, frame_count=4, speed=0.1, loop=True),
            "run": PlayerAnimator(sheet_path, start_frame=8, frame_count=6, speed=0.2, loop=True),
            "jump": PlayerAnimator(sheet_path, start_frame=14, frame_count=4, speed=0.15, loop=False),
            "attack": PlayerAnimator(sheet_path, start_frame=42, frame_count=5, speed=0.2, loop=False),
            "special": PlayerAnimator(sheet_path, start_frame=47, frame_count=6, speed=0.15, loop=False),
            "legendary": PlayerAnimator(sheet_path, start_frame=53, frame_count=6, speed=0.25, loop=False)
        }
        
        self.combo_step = 0
        self.combo_timer = 0
        self.attack_timer = 0
        self.special_timer = 0
        self.special_hit_timer = 0
        self.special_hits_done = 0
        self.legendary_timer = 0
        self.legendary_phase = 0
        self.legendary_done = False
        self.energy_timer = 0
        self.sword_flash = 0
        self.hit_count = 0
        self.last_hit_time = 0

    def get_hitbox(self):
        if self.crouching:
            crouch_h = 52
            return pygame.Rect(int(self.x), int(self.y + (self.height - crouch_h)), int(self.width), crouch_h)
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def jump(self):
        if self.jumps_left <= 0: return
        self.vel_y = self.jump_power
        self.on_ground = False
        self.jumps_left -= 1

    def update(self, keys, enemies, touch_buttons=None):
        if touch_buttons is None:
            touch_buttons = set()

        self.crouching = (
            "down" in touch_buttons
            or keys[pygame.K_DOWN]
            or keys[pygame.K_s]
        )

        self.vel_x = 0
        current_speed = self.speed

        k_left = game_settings["keys"]["left"] if "game_settings" in globals() else pygame.K_a
        k_right = game_settings["keys"]["right"] if "game_settings" in globals() else pygame.K_d
        if keys[k_left] or keys[pygame.K_LEFT] or "back" in touch_buttons:
            self.vel_x = -current_speed
            self.facing = -1
        if keys[k_right] or keys[pygame.K_RIGHT] or "forward" in touch_buttons:
            self.vel_x = current_speed
            self.facing = 1

        if self.on_ground: self.knockback_x *= 0.8
        else: self.knockback_x *= 0.95
            
        if abs(self.knockback_x) < 0.5: self.knockback_x = 0

        total_vel_x = self.vel_x + self.knockback_x
        self.vel_y += self.gravity

        self.x += total_vel_x
        self.x, hit_wall = stage_layout.get_valid_x(self.x, self.y, self.width, self.height, total_vel_x)
        self.y += self.vel_y

        current_ground_y = stage_layout.get_ground_y(self.x, self.width, self.height, self.y)
        self.current_floor_y = current_ground_y
        ground_y = current_ground_y - self.height

        if self.vel_y >= 0 and self.y >= ground_y - 25:
            self.y = ground_y
            self.vel_y = 0
            if not self.on_ground: self.jumps_left = self.max_jumps
            self.on_ground = True
        else:
            self.on_ground = False

        stage_limit = max(WIDTH + 100, int(getattr(stage_layout, "stage_length", WORLD_WIDTH)))
        self.x = max(0, min(self.x, stage_limit - self.width))

        if self.combo_timer > 0: self.combo_timer -= 1
        else:
            if self.attack_timer <= 0: self.combo_step = 0

        if self.attack_timer > 0: self.attack_timer -= 1

        if self.special_timer > 0:
            self.special_timer -= 1
            self.special_hit_timer -= 1
            if self.special_hit_timer <= 0:
                self.special_hit_timer = 8
                self.special_hits_done += 1
                skill_bonus = int(game_progress.get("sword_level", 0)) * 8 + int(game_progress.get("berserk_level", 0)) * 5
                self.damage_nearby(enemies, 25 + skill_bonus)
            if self.special_hits_done >= 7:
                self.special_timer = 0

        if self.legendary_timer > 0:
            self.legendary_timer -= 1
            if self.legendary_timer > 70: self.legendary_phase = 1
            elif self.legendary_timer > 25: self.legendary_phase = 2
            else:
                self.legendary_phase = 3
                if not self.legendary_done:
                    self.legendary_done = True
                    self.energy_timer = 35
                    ultimate_bonus = int(game_progress.get("sword_level", 0)) * 15 + int(game_progress.get("berserk_level", 0)) * 10
                    self.damage_all_visible(enemies, 100 + ultimate_bonus)

        if self.energy_timer > 0: self.energy_timer -= 1
        if self.shield_timer > 0: self.shield_timer -= 1
        if self.shield_cooldown > 0: self.shield_cooldown -= 1
        if self.legendary_cooldown > 0: self.legendary_cooldown -= 1

        if self.on_ground and self.current_floor_y <= GROUND_Y + 20:
            self.last_safe_pos = (int(self.x), int(self.y))

        if self.legendary_timer > 0: self.state = "legendary"
        elif self.special_timer > 0: self.state = "special"
        elif self.attack_timer > 0: self.state = "attack"
        elif not self.on_ground: self.state = "jump"
        elif self.crouching and self.on_ground: self.state = "crouch"
        elif abs(self.vel_x) > 0: self.state = "run"
        else: self.state = "idle"

    def normal_attack(self, enemies):
        if self.special_timer > 0 or self.legendary_timer > 0 or self.attack_timer > 0: return
        self.combo_step += 1
        if self.combo_step > 4: self.combo_step = 1
        if "attack" in self.animations and self.animations["attack"].frames:
            anim = self.animations["attack"]
            anim.current_frame = 0
            self.attack_timer = int(len(anim.frames) / anim.speed)
        else:
            self.attack_timer = 15
        self.combo_timer = self.attack_timer + 15
        sword_bonus = int(game_progress.get("sword_level", 0)) * 8
        berserk_bonus = int(game_progress.get("berserk_level", 0)) * 5
        bonus = sword_bonus + berserk_bonus
        if self.combo_step == 1: self.damage_nearby(enemies, 20 + bonus, is_heavy=False)
        elif self.combo_step == 2: self.damage_nearby(enemies, 22 + bonus, is_heavy=False)
        elif self.combo_step == 3: self.damage_nearby(enemies, 24 + bonus, is_heavy=False)
        elif self.combo_step == 4: self.damage_nearby(enemies, 35 + bonus * 2, is_heavy=True)
    
    def special_attack(self):
        if self.attack_timer > 0 or self.legendary_timer > 0 or self.special_timer > 0: return
        if "special" in self.animations and self.animations["special"].frames:
            anim = self.animations["special"]
            anim.current_frame = 0
            self.special_timer = int(len(anim.frames) / anim.speed)
        else:
            self.special_timer = 65
        self.special_hit_timer = 1
        self.special_hits_done = 0
        self.state = "special"

    def legendary_attack(self):
        if self.attack_timer > 0 or self.special_timer > 0 or self.legendary_timer > 0 or self.legendary_cooldown > 0: return
        if "legendary" in self.animations and self.animations["legendary"].frames:
            anim = self.animations["legendary"]
            anim.current_frame = 0
            self.legendary_timer = max(36, int(len(anim.frames) / anim.speed))
        else:
            self.legendary_timer = 36
        self.legendary_cooldown = 120 * FPS
        self.legendary_phase = 1
        self.legendary_done = False
        self.energy_timer = 0
        self.state = "legendary"

    def activate_shield(self):
        if game_progress.get("shield_unlocked", False) and self.shield_timer <= 0 and self.shield_cooldown <= 0:
            shield_level = max(1, min(5, int(game_progress.get("shield_level", 1))))
            shield_seconds = min(60, 10 + shield_level * 10)
            self.shield_timer = shield_seconds * FPS
            self.shield_cooldown = 120 * FPS

    def throw_spear(self):
        if not game_progress.get("spear_unlocked", False):
            return
        if int(game_progress.get("arrow_ammo", 0)) <= 0 or len(spear_projectiles) >= 3:
            return
        spear_projectiles.append({
            "x": self.x + (self.width if self.facing > 0 else -20),
            "y": self.y + 42,
            "vx": self.facing * 18,
            "damage": 65 + int(game_progress.get("sword_level", 0)) * 8,
        })
        game_progress["arrow_ammo"] = max(0, int(game_progress.get("arrow_ammo", 0)) - 1)
        save_progress(game_progress)

    def damage_nearby(self, enemies, damage, is_heavy=False):
        attack_range = 150
        for enemy in enemies:
            if enemy.health <= 0: continue
            dx = enemy.x - self.x
            if self.facing == 1:
                if dx < -20 or dx > attack_range: continue
            else:
                if dx > 20 or dx < -attack_range: continue
            hit_dir = 1 if enemy.x > self.x else -1
            enemy.take_damage(damage, hit_dir, is_heavy=is_heavy)

    def damage_all_visible(self, enemies, damage):
        for enemy in enemies:
            if enemy.health <= 0: continue
            screen_x = enemy.x - camera_x
            if -100 <= screen_x <= WIDTH + 100:
                hit_dir = 1 if enemy.x > self.x else -1
                enemy.take_damage(damage, hit_dir, is_heavy=True)

    def draw_animation(self, surface, sx, sy):
        current_anim = "idle" if self.state == "crouch" else self.state
        if current_anim not in self.animations or not self.animations[current_anim].frames:
            current_anim = "idle"
        animator = self.animations.get(current_anim)
        if animator and animator.frames:
            animator.update()
            img = animator.get_current_image(facing_right=(self.facing == 1))
            target_height = 95 if self.state == "crouch" else 140
            if self.legendary_timer > 0:
                target_height = 280  
            frame_index = max(0, min(len(animator.frames) - 1, int(animator.current_frame)))
            cache_key = (animator.frame_keys[frame_index], self.facing, target_height)
            scaled = PlayerAnimator._scaled_cache.get(cache_key)
            if scaled is None:
                ratio = target_height / max(1, img.get_height())
                target_width = max(1, int(img.get_width() * ratio))
                scaled = pygame.transform.scale(img, (target_width, target_height))
                PlayerAnimator._scaled_cache[cache_key] = scaled
            img = scaled
            img_rect = img.get_rect(midbottom=(sx + self.width // 2, sy + self.height + 15))
            surface.blit(img, img_rect)
        else:
            body_x = sx + self.width // 2
            body_y = sy + 25
            pygame.draw.rect(surface, BLUE, (body_x - 20, body_y + 20, 40, 55))

    def draw(self, surface):
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        self.draw_animation(surface, sx, sy)

        if self.shield_timer > 0:
            if self.shield_timer > 60 or (self.shield_timer // 4) % 2 == 0:
                hb = self.get_hitbox()
                cx = int(hb.centerx - camera_x)
                cy = int(hb.centery - camera_y)
                rad = max(hb.width, hb.height) // 2 + 18
                shield_surf = pygame.Surface((rad * 2 + 8, rad * 2 + 8), pygame.SRCALPHA)
                pygame.draw.circle(shield_surf, (70, 220, 255, 65), (rad + 4, rad + 4), rad)
                pygame.draw.circle(shield_surf, (255, 230, 90, 210), (rad + 4, rad + 4), rad, 3)
                surface.blit(shield_surf, (cx - rad - 4, cy - rad - 4))


def draw_legendary_effect(player):
    if player.legendary_timer <= 0: return
    darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    darkness.fill((25, 5, 5, 160)) 
    screen.blit(darkness, (0, 0))
    px = int(player.x - camera_x + 25)
    py = int(player.y - camera_y + 45)
    radius = 120
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 60, 0, 50), (radius, radius), radius)      
    pygame.draw.circle(glow, (255, 20, 0, 90), (radius, radius), radius // 2) 
    screen.blit(glow, (px - radius, py - radius))

    if player.legendary_phase >= 1 and player.legendary_timer > 0:
        gather_radius = player.legendary_timer * 3.5 
        for i in range(15):
            speed = pygame.time.get_ticks() * 0.005
            angle = speed + i * (math.pi * 2 / 15)
            wave = math.sin(speed * 6 + i) * 20
            current_dist = gather_radius + wave
            if current_dist > 10: 
                fx = px + math.cos(angle) * current_dist
                fy = py + math.sin(angle) * current_dist
                color_choice = i % 3
                if color_choice == 0: fire_color = (255, 40, 0)   
                elif color_choice == 1: fire_color = (255, 120, 0) 
                else: fire_color = (255, 220, 0)                  
                size = 5 + (i % 4)
                pygame.draw.circle(screen, fire_color, (int(fx), int(fy)), size)
                trail_x = fx + math.cos(angle + 0.5) * 25
                trail_y = fy + math.sin(angle + 0.5) * 25
                pygame.draw.line(screen, (200, 20, 0), (int(fx), int(fy)), (int(trail_x), int(trail_y)), 3)

    if player.energy_timer > 0:
        start_x = px + player.facing * 30
        start_y = py
        end_x = start_x + player.facing * WIDTH
        pygame.draw.line(screen, (220, 30, 0), (start_x, start_y), (end_x, start_y), 50)  
        pygame.draw.line(screen, (255, 120, 0), (start_x, start_y), (end_x, start_y), 30) 
        pygame.draw.line(screen, (255, 255, 100), (start_x, start_y), (end_x, start_y), 12) 
        for i in range(18):
            x = start_x + player.facing * (i * 70 + 20)
            y = start_y + math.sin(i * 4 + pygame.time.get_ticks() * 0.04) * 60
            size = 4 + (i % 5)
            pygame.draw.circle(screen, (255, 200, 0), (int(x), int(y)), size)
            pygame.draw.circle(screen, (255, 50, 0), (int(x), int(y)), size + 4, 2)

CONTROL_RECTS = {
    "back": pygame.Rect(30, HEIGHT - 115, 80, 80),
    "forward": pygame.Rect(120, HEIGHT - 115, 80, 80),
    "down": pygame.Rect(75, HEIGHT - 215, 80, 80),
    "jump": pygame.Rect(900, HEIGHT - 115, 80, 80),
    "attack": pygame.Rect(990, HEIGHT - 115, 80, 80),
    "special": pygame.Rect(1080, HEIGHT - 215, 80, 80),
    "legendary": pygame.Rect(1170, HEIGHT - 115, 80, 80),
    "spear": pygame.Rect(1170, HEIGHT - 215, 80, 80),
}

CONTROL_OPACITY = {}
TOUCH_MODE = "buttons"

JOYSTICK_CENTER = [160, 570]
JOYSTICK_RADIUS = 75
JOYSTICK_OPACITY = 180

def apply_touch_settings(settings):
    global CONTROL_RECTS, CONTROL_OPACITY, TOUCH_MODE
    global JOYSTICK_CENTER, JOYSTICK_RADIUS, JOYSTICK_OPACITY
    config = settings.get("touch_controls", {})
    positions = config.get("positions", {})
    opacity = config.get("opacity", {})
    TOUCH_MODE = config.get("mode", "buttons")
    joystick = config.get("joystick", {})
    JOYSTICK_CENTER = [int(joystick.get("x", 160)), int(joystick.get("y", 570))]
    JOYSTICK_RADIUS = max(30, int(joystick.get("radius", 75)))
    JOYSTICK_OPACITY = max(0, min(255, int(opacity.get("joystick", 180))))

    defaults = {
        "back": (30, HEIGHT - 115, 80, 80),
        "forward": (120, HEIGHT - 115, 80, 80),
        "down": (75, HEIGHT - 215, 80, 80),
        "jump": (900, HEIGHT - 115, 80, 80),
        "attack": (990, HEIGHT - 115, 80, 80),
        "special": (1080, HEIGHT - 215, 80, 80),
        "legendary": (1170, HEIGHT - 115, 80, 80),
        "spear": (1170, HEIGHT - 215, 80, 80),
    }

    for name, default in defaults.items():
        data = positions.get(name, {})
        x = int(data.get("x", default[0]))
        y = int(data.get("y", default[1]))
        w = max(20, int(data.get("w", default[2])))
        h = max(20, int(data.get("h", default[3])))
        CONTROL_RECTS[name] = pygame.Rect(x, y, w, h)

    for name in defaults:
        CONTROL_OPACITY[name] = max(0, min(255, int(opacity.get(name, 190))))

CONTROL_SYMBOLS = {"back": "<", "forward": ">", "down": "v", "jump": "^", "attack": "X", "special": "*", "legendary": "!", "spear": ">"}
CONTROL_LABELS = {"back": "BACK", "forward": "MOVE", "down": "CROUCH", "jump": "JUMP", "attack": "ATTACK", "special": "SPECIAL", "legendary": "ULTIMATE", "spear": "ARROWS"}

def get_control_at(pos):
    for name, rect in CONTROL_RECTS.items():
        if TOUCH_MODE == "joystick" and name in ("back", "forward", "down", "jump"):
            continue
        if name == "spear" and not game_progress.get("spear_unlocked", False):
            continue
        if rect.collidepoint(pos):
            return name
    return None

TOUCH_SYMBOL_FONT = pygame.font.SysFont("arial", 32, bold=True)
TOUCH_LABEL_FONT = get_arabic_font(12)
TOUCH_BUTTON_CACHE = {}
JOYSTICK_BASE_CACHE = {}
HUD_FONT = get_arabic_font(23)
BUTTON_FONT = get_arabic_font(28)

ACTIVE_UPDATE_BEHIND = 900
ACTIVE_UPDATE_AHEAD = 1400
DRAW_MARGIN_X = 260

PAUSE_BTN_RECT = pygame.Rect(WIDTH - 75, 18, 54, 54)
SKILL_SHIELD_RECT = pygame.Rect(WIDTH - 250, 18, 76, 54)
SKILL_SPEAR_RECT = pygame.Rect(WIDTH - 165, 18, 76, 54)
PAUSE_RESUME_RECT = pygame.Rect(WIDTH // 2 - 170, HEIGHT // 2 - 35, 340, 64)
PAUSE_MENU_RECT = pygame.Rect(WIDTH // 2 - 170, HEIGHT // 2 + 50, 340, 64)
PAUSE_AR_CACHE = {}

def get_pause_ar_img(name):
    if name not in PAUSE_AR_CACHE:
        p = asset_path("ui_ar", name)
        PAUSE_AR_CACHE[name] = pygame.image.load(p).convert_alpha() if os.path.exists(p) else None
    return PAUSE_AR_CACHE[name]

def draw_heart_icon(surface, x, y, size, filled=True):
    col = (235, 45, 65) if filled else (75, 75, 85)
    r = size // 4
    pygame.draw.circle(surface, col, (x - r, y - r // 2), r)
    pygame.draw.circle(surface, col, (x + r, y - r // 2), r)
    pts = [(x - size // 2, y - r // 4), (x + size // 2, y - r // 4), (x, y + size // 2)]
    pygame.draw.polygon(surface, col, pts)
    pygame.draw.polygon(surface, WHITE, pts, 1)

def draw_pause_button_and_overlay(paused, settings):
    pygame.draw.ellipse(screen, (45, 55, 75), PAUSE_BTN_RECT)
    pygame.draw.ellipse(screen, WHITE, PAUSE_BTN_RECT, 2)
    cx, cy = PAUSE_BTN_RECT.center
    pygame.draw.rect(screen, WHITE, (cx - 9, cy - 11, 6, 22), border_radius=2)
    pygame.draw.rect(screen, WHITE, (cx + 3, cy - 11, 6, 22), border_radius=2)

    if not paused:
        return

    veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    veil.fill((10, 14, 24, 195))
    screen.blit(veil, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 140, 440, 290)
    pygame.draw.rect(screen, (30, 36, 52), panel, border_radius=18)
    pygame.draw.rect(screen, GOLD, panel, 3, border_radius=18)

    is_ar = settings.get("language", "ar") == "ar"
    title_img = get_pause_ar_img("pause_title.png") if is_ar else None
    if title_img:
        screen.blit(title_img, title_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 90)))
    else:
        t_surf = BUTTON_FONT.render("PAUSED", True, GOLD)
        screen.blit(t_surf, t_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 90)))

    pygame.draw.rect(screen, (45, 150, 75), PAUSE_RESUME_RECT, border_radius=12)
    pygame.draw.rect(screen, WHITE, PAUSE_RESUME_RECT, 2, border_radius=12)
    res_img = get_pause_ar_img("pause_resume.png") if is_ar else None
    if res_img:
        screen.blit(res_img, res_img.get_rect(center=PAUSE_RESUME_RECT.center))
    else:
        r_surf = BUTTON_FONT.render("Resume", True, WHITE)
        screen.blit(r_surf, r_surf.get_rect(center=PAUSE_RESUME_RECT.center))

    pygame.draw.rect(screen, (185, 55, 55), PAUSE_MENU_RECT, border_radius=12)
    pygame.draw.rect(screen, WHITE, PAUSE_MENU_RECT, 2, border_radius=12)
    menu_img = get_pause_ar_img("pause_menu.png") if is_ar else None
    if menu_img:
        screen.blit(menu_img, menu_img.get_rect(center=PAUSE_MENU_RECT.center))
    else:
        m_surf = BUTTON_FONT.render("Main Menu", True, WHITE)
        screen.blit(m_surf, m_surf.get_rect(center=PAUSE_MENU_RECT.center))

def activate_control(name):
    if name == "jump": player.jump()
    elif name == "attack": player.normal_attack(enemies)
    elif name == "special": player.special_attack()
    elif name == "legendary": player.legendary_attack()
    elif name == "spear" and game_progress.get("spear_unlocked", False): player.throw_spear()

def draw_touch_controls(pressed_buttons):
    symbol_font = TOUCH_SYMBOL_FONT
    label_font = TOUCH_LABEL_FONT

    for name, rect in CONTROL_RECTS.items():
        if name == "spear" and not game_progress.get("spear_unlocked", False):
            continue
        if TOUCH_MODE == "joystick" and name in ("back", "forward", "down", "jump"):
            continue
        pressed = name in pressed_buttons
        if pressed: color = (55, 145, 210)
        elif name in ("special", "legendary"): color = (105, 55, 145)
        elif name == "attack": color = (165, 65, 55)
        else: color = (65, 75, 90)

        opacity = CONTROL_OPACITY.get(name, 190)
        arabic_labels = {"back": "يسار", "forward": "يمين", "down": "انحناء", "jump": "قفز", "attack": "هجوم", "special": "خاص", "legendary": "قاضية", "spear": "سهام"}
        label_text = arabic_labels.get(name, CONTROL_LABELS[name]) if game_settings.get("language", "ar") == "ar" else CONTROL_LABELS[name]
        cache_key = (name, rect.width, rect.height, color, opacity, label_text)
        button_surface = TOUCH_BUTTON_CACHE.get(cache_key)
        if button_surface is None:
            button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            local_rect = button_surface.get_rect()
            pygame.draw.ellipse(button_surface, (*color, opacity), local_rect)
            pygame.draw.ellipse(button_surface, (255, 255, 255, opacity), local_rect, 3)
            symbol = symbol_font.render(CONTROL_SYMBOLS[name], True, WHITE)
            symbol.set_alpha(opacity)
            button_surface.blit(symbol, symbol.get_rect(center=(rect.width // 2, rect.height // 2 - 10)))
            label = label_font.render(fix_text(label_text), True, WHITE)
            label.set_alpha(opacity)
            button_surface.blit(label, label.get_rect(center=(rect.width // 2, rect.height - 12)))
            TOUCH_BUTTON_CACHE[cache_key] = button_surface
        screen.blit(button_surface, rect.topleft)

    if TOUCH_MODE == "joystick":
        cx, cy = JOYSTICK_CENTER
        radius = JOYSTICK_RADIUS
        base_key = (radius, JOYSTICK_OPACITY)
        base = JOYSTICK_BASE_CACHE.get(base_key)
        if base is None:
            base = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
            center = (radius + 4, radius + 4)
            pygame.draw.circle(base, (55, 65, 85, JOYSTICK_OPACITY), center, radius)
            pygame.draw.circle(base, (230, 235, 245, JOYSTICK_OPACITY), center, radius, 4)
            JOYSTICK_BASE_CACHE[base_key] = base
        screen.blit(base, (cx - radius - 4, cy - radius - 4))

        thumb_x, thumb_y = cx, cy
        if joystick_fingers or joystick_mouse_pos is not None:
            finger_pos = next(iter(joystick_fingers.values())) if joystick_fingers else joystick_mouse_pos
            dx = finger_pos[0] - cx
            dy = finger_pos[1] - cy
            distance = math.hypot(dx, dy)
            max_distance = radius * 0.55
            if distance > max_distance and distance > 0:
                scale = max_distance / distance
                dx *= scale
                dy *= scale
            thumb_x = int(cx + dx)
            thumb_y = int(cy + dy)

        thumb_radius = max(16, int(radius * 0.34))
        pygame.draw.circle(screen, (80, 155, 220), (thumb_x, thumb_y), thumb_radius)
        pygame.draw.circle(screen, WHITE, (thumb_x, thumb_y), thumb_radius, 3)

def draw_skill_buttons():
    if game_progress.get("shield_unlocked", False):
        color = (35, 130, 190) if player.shield_timer <= 0 else (35, 170, 120)
        pygame.draw.rect(screen, color, SKILL_SHIELD_RECT, border_radius=10)
        txt = HUD_FONT.render(fix_text("درع"), True, WHITE)
        screen.blit(txt, txt.get_rect(center=SKILL_SHIELD_RECT.center))



def create_stage_enemies(stage, stage_layout):
    from enemies import Enemy
    import random

    enemies = []
    ground_y = 570
    stage_end = max(1200, int(getattr(stage_layout, "gate_x", 34200)) - 420)

    # ??????? ?????? ???????? ???????? ??????? ?? ????? ???? ???????.
    excluded = set()
    for group in (
        getattr(stage_layout, "bridge_rects", []),
        getattr(stage_layout, "dynamic_plat_rects", [])
    ):
        for r in group:
            excluded.add((r.x, r.y, r.width, r.height))

    stable_platforms = []
    for platform in stage_layout.platforms:
        key = (platform.x, platform.y, platform.width, platform.height)
        if key in excluded:
            continue
        if platform.width < 150:
            continue
        if platform.top < 0 or platform.top > ground_y + 5:
            continue
        stable_platforms.append(platform)

    if not stable_platforms:
        print("WARNING: No safe stable platforms found for enemies.")
        return enemies

    used_positions = []

    def find_safe(target_x, width, height, min_gap=150):
        best = None

        for platform in stable_platforms:
            if platform.width < width + 30:
                continue

            left = platform.left + 12
            right = platform.right - width - 12

            if right < left:
                continue

            # ???? ?????? ??? ?????? ?????? ?????? ?????? ???????.
            candidates = {max(left, min(right, int(target_x)))}
            step = 45
            for x in range(left, right + 1, step):
                candidates.add(x)

            for x in candidates:
                if x < 100 or x > stage_end:
                    continue

                if any(abs(x - old_x) < min_gap for old_x in used_positions):
                    continue

                body = pygame.Rect(
                    int(x), int(platform.top - height),
                    int(width), int(height)
                )

                # ??? ?? ???? ????? ????? ??? ???? ????? ???????.
                if x + width > platform.right - 5:
                    continue

                danger = False

                for hazard in stage_layout.hazards:
                    hr = hazard["rect"]
                    if body.inflate(100, 35).colliderect(hr):
                        danger = True
                        break

                if danger:
                    continue

                for acid in stage_layout.acid_pools:
                    acid_rect = pygame.Rect(
                        acid.x - 60, acid.y - 20,
                        acid.width + 120, acid.height + 40
                    )
                    if body.colliderect(acid_rect):
                        danger = True
                        break

                if danger:
                    continue

                for mountain in stage_layout.mountains:
                    if abs(x - mountain["peak_x"]) < 170:
                        danger = True
                        break

                if danger:
                    continue

                distance = abs(x - target_x)
                if best is None or distance < best[0]:
                    best = (distance, x, platform.top)

        if best is None:
            return None

        _, spawn_x, floor_y = best
        used_positions.append(spawn_x)
        return spawn_x, floor_y

    # 30 ?????? ?????? ?? ????? ???? ???.
    slots = 30
    for index in range(slots):
        target_x = int(
            750 + index * (stage_end - 1500) / max(1, slots - 1)
        )

        position = find_safe(target_x, 55, 90, min_gap=180)

        if position is None:
            continue

        spawn_x, spawn_floor = position
        enemies.append(Enemy(spawn_x, "skeleton", spawn_floor, stage))

    # ????? ?????? ??????? ??????? ??? ????? ??????? ???.
    x_pos = 1200
    while x_pos < stage_end:
        rand_type = random.randint(1, 100)

        if rand_type <= 58:
            e_type = "soldier"
        elif rand_type <= 82:
            e_type = "commander"
        else:
            e_type = "guard"

        enemy_width = 50
        enemy_height = 90

        position = find_safe(
            x_pos, enemy_width, enemy_height, min_gap=135
        )

        if position is not None:
            spawn_x, spawn_floor = position
            enemies.append(Enemy(spawn_x, e_type, spawn_floor, stage))

        x_pos += random.randint(950, 1450)

    # ????? ????? ???? ??? ???? ????? ????? ??? ????? ???????.
    king_target = int(getattr(stage_layout, "gate_x", 34200)) - 170
    king_position = find_safe(
        king_target, 100, 150, min_gap=100
    )

    if king_position is not None:
        king_x, king_floor = king_position
        enemies.append(Enemy(king_x, "king", king_floor, stage))
    else:
        print("WARNING: No safe location found for the king.")

    return enemies

menu = MainMenu(screen)
starting_stage = menu.run()
game_settings = load_settings()
game_progress = load_progress()
apply_touch_settings(game_settings)

world = World(stage=starting_stage)
stage_layout = StageLayout(stage=starting_stage)
player = Player()
enemies = create_stage_enemies(starting_stage, stage_layout)
spear_projectiles = []
arrows = []
stage_reward_claimed = False

current_stage = starting_stage
game_progress["arrow_ammo"] = 30
king_defeated = False

# كل إصبع له معرّف مستقل. استخدام touch_id مع finger_id يمنع
# تصادم المعرّفات عند وجود أكثر من مصدر لمس.
touch_assignments = {}
mouse_control = None

joystick_fingers = {}
joystick_mouse_pos = None


def get_finger_key(event):
    return (
        getattr(event, "touch_id", 0),
        getattr(event, "finger_id", 0),
    )


def get_finger_position(event):
    # إحداثيات FINGER تكون نسبية إلى الشاشة، ونحوّلها إلى مساحة اللعب 1280x720.
    return (
        max(0, min(WIDTH - 1, int(event.x * WIDTH))),
        max(0, min(HEIGHT - 1, int(event.y * HEIGHT))),
    )
joystick_jump_latched = False
joystick_auto_jump = False
paused = False

def return_to_main_menu():
    global starting_stage, game_settings, current_stage, king_defeated, enemies, paused, camera_x, camera_y, game_progress, spear_projectiles, arrows, stage_reward_claimed, pruned_world_x, last_prune_camera_x
    paused = False
    touch_assignments.clear()
    joystick_fingers.clear()
    menu = MainMenu(screen)
    starting_stage = menu.run()
    game_settings = load_settings()
    game_progress = load_progress()
    spear_projectiles = []
    arrows = []
    stage_reward_claimed = False
    apply_touch_settings(game_settings)
    current_stage = starting_stage
    world.set_stage(current_stage)
    stage_layout.__init__(stage=current_stage)
    player.__init__()
    enemies = create_stage_enemies(current_stage, stage_layout)
    camera_x = 0
    camera_y = 0
    pruned_world_x = 0
    last_prune_camera_x = 0
    king_defeated = False

running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if paused:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    paused = False
            elif not IS_ANDROID and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if PAUSE_RESUME_RECT.collidepoint(event.pos) or PAUSE_BTN_RECT.collidepoint(event.pos):
                    paused = False
                elif PAUSE_MENU_RECT.collidepoint(event.pos):
                    return_to_main_menu()
            elif event.type == pygame.FINGERDOWN:
                fpos = get_finger_position(event)
                if PAUSE_RESUME_RECT.collidepoint(fpos) or PAUSE_BTN_RECT.collidepoint(fpos):
                    paused = False
                elif PAUSE_MENU_RECT.collidepoint(fpos):
                    return_to_main_menu()
            continue

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                paused = True
                continue
            if event.key == pygame.K_ESCAPE: running = False
            k_map = game_settings["keys"]
            if event.key in (k_map["jump"], pygame.K_UP): player.jump()
            if event.key == k_map["attack"]: player.normal_attack(enemies)
            if event.key == k_map["special"]: player.special_attack()
            if event.key == k_map["legendary"]: player.legendary_attack()
            if event.key == pygame.K_u: player.activate_shield()
            if event.key == pygame.K_i: player.throw_spear()

        if event.type == pygame.FINGERDOWN:
            pointer_id = get_finger_key(event)
            pos = get_finger_position(event)

            if PAUSE_BTN_RECT.collidepoint(pos):
                paused = True
                continue
            if SKILL_SHIELD_RECT.collidepoint(pos):
                player.activate_shield()
                continue

            if TOUCH_MODE == "joystick":
                cx, cy = JOYSTICK_CENTER
                if math.hypot(pos[0] - cx, pos[1] - cy) <= JOYSTICK_RADIUS * 1.45:
                    joystick_fingers[pointer_id] = pos
                else:
                    name = get_control_at(pos)
                    if name:
                        touch_assignments[pointer_id] = name
                        activate_control(name)
            else:
                name = get_control_at(pos)
                if name:
                    touch_assignments[pointer_id] = name
                    activate_control(name)

        elif event.type == pygame.FINGERMOTION:
            pointer_id = get_finger_key(event)
            pos = get_finger_position(event)

            if pointer_id in joystick_fingers:
                joystick_fingers[pointer_id] = pos
            elif pointer_id in touch_assignments:
                name = get_control_at(pos)
                if name:
                    touch_assignments[pointer_id] = name
                else:
                    touch_assignments.pop(pointer_id, None)

        elif event.type == pygame.FINGERUP:
            pointer_id = get_finger_key(event)
            joystick_fingers.pop(pointer_id, None)
            touch_assignments.pop(pointer_id, None)

        elif not IS_ANDROID and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if PAUSE_BTN_RECT.collidepoint(event.pos):
                paused = True
                continue
            if SKILL_SHIELD_RECT.collidepoint(event.pos):
                player.activate_shield()
                continue
            if TOUCH_MODE == "joystick":
                cx, cy = JOYSTICK_CENTER
                if math.hypot(event.pos[0] - cx, event.pos[1] - cy) <= JOYSTICK_RADIUS * 1.8:
                    joystick_mouse_pos = event.pos
                    mouse_control = None
                else:
                    mouse_control = get_control_at(event.pos)
                    if mouse_control:
                        activate_control(mouse_control)
            else:
                mouse_control = get_control_at(event.pos)
                if mouse_control:
                    activate_control(mouse_control)

        elif not IS_ANDROID and event.type == pygame.MOUSEMOTION:
            if joystick_mouse_pos is not None:
                joystick_mouse_pos = event.pos
            elif mouse_control is not None and pygame.mouse.get_pressed()[0]:
                mouse_control = get_control_at(event.pos)

        elif not IS_ANDROID and event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mouse_control = None
            joystick_mouse_pos = None

    keys = pygame.key.get_pressed()
    pressed_buttons = set(touch_assignments.values())
    if mouse_control:
        pressed_buttons.add(mouse_control)

    joystick_up = False
    if TOUCH_MODE == "joystick" and (joystick_fingers or joystick_mouse_pos is not None):
        finger_pos = next(iter(joystick_fingers.values())) if joystick_fingers else joystick_mouse_pos
        dx = finger_pos[0] - JOYSTICK_CENTER[0]
        dy = finger_pos[1] - JOYSTICK_CENTER[1]
        nx = dx / JOYSTICK_RADIUS
        ny = dy / JOYSTICK_RADIUS
        if nx < -0.35: pressed_buttons.add("back")
        elif nx > 0.35: pressed_buttons.add("forward")
        if ny > 0.45: pressed_buttons.add("down")
        if ny < -0.55 and abs(nx) < 0.85: joystick_up = True

    if joystick_up and not joystick_jump_latched:
        joystick_auto_jump = True
    joystick_jump_latched = joystick_up
    
    if joystick_auto_jump:
        if player.jumps_left > 0 and (player.on_ground or player.vel_y >= 0):
            player.jump()
        elif player.jumps_left <= 0:
            joystick_auto_jump = False
    
    if not paused:
        player.update(keys, enemies, pressed_buttons)
        # لا تسمح بالعودة إلى منطقة تم حذفها من الذاكرة.
        player.x = max(player.x, pruned_world_x)
        stage_layout.check_hazards(player)

        if player.y > GROUND_Y + 350:
            if player.shield_timer > 0:
                rx, ry = stage_layout.find_safe_respawn(player.last_safe_pos[0], player.width, player.height)
                player.x, player.y = rx, ry
                player.vel_y = 0
            else:
                player.health = 0

        update_min_x = player.x - ACTIVE_UPDATE_BEHIND
        update_max_x = player.x + ACTIVE_UPDATE_AHEAD

        for enemy in enemies:
            enemy_busy = (
                getattr(enemy, "state", "idle") in ("hit", "attack", "dead")
                or abs(getattr(enemy, "vel_y", 0)) > 0.1
                or abs(getattr(enemy, "knockback_x", 0)) > 0.1
                or getattr(enemy, "hurt_timer", 0) > 0
            )
            if not (update_min_x <= enemy.x <= update_max_x or enemy_busy):
                continue

            enemy.update(player.x, player.y, stage_layout)

            if enemy.enemy_type in ("guard", "king") and enemy.is_alive():
                enemy.arrow_cooldown -= 1
                dx = (player.x + player.width / 2) - (enemy.x + enemy.width / 2)
                dy = (player.y + player.height / 2) - (enemy.y + enemy.height / 2)
                if abs(dx) < 760 and abs(dy) < 260 and enemy.arrow_cooldown <= 0:
                    length = max(1.0, math.hypot(dx, dy))
                    stage_power = 1.0 + (current_stage - 1) * 0.10
                    speed = (10 if enemy.enemy_type == "guard" else 12) + current_stage * 0.12
                    base_arrow_damage = 12 if enemy.enemy_type == "guard" else 22
                    arrows.append({"x": enemy.x + enemy.width / 2, "y": enemy.y + 42,
                                   "vx": dx / length * speed, "vy": dy / length * speed,
                                   "damage": int(base_arrow_damage * stage_power)})
                    enemy.arrow_cooldown = 115 if enemy.enemy_type == "guard" else 90

            if enemy.is_alive() and enemy.state != "dead":
                player_rect = player.get_hitbox()
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)

                if player_rect.colliderect(enemy_rect) and player.shield_timer <= 0:
                    current_time = time.time()
                    if current_time - player.last_hit_time > 0.5:
                        if current_time - player.last_hit_time > 2.0:
                            player.hit_count = 0
                        player.health -= enemy.damage
                        player.hit_count += 1
                        player.last_hit_time = current_time
                        if player.hit_count >= 3:
                            hit_dir = 1 if player.x < enemy.x else -1
                            player.vel_y = -12
                            player.knockback_x = -15 * hit_dir
                            player.on_ground = False
                            player.hit_count = 0 

        # Reward each defeated enemy exactly once and persist the balance.
        for enemy in enemies:
            if not enemy.is_alive() and not getattr(enemy, "reward_claimed", False):
                enemy.reward_claimed = True
                reward = 6 if enemy.enemy_type == "king" else (4 if enemy.enemy_type == "guard" else 2)
                add_coins(game_progress, reward)
        enemies = [enemy for enemy in enemies if not getattr(enemy, "remove_from_world", False)]

        # Spear projectiles travel forward and damage the first enemy they hit.
        for spear in spear_projectiles[:]:
            spear["x"] += spear["vx"]
            spear_rect = pygame.Rect(int(spear["x"]), int(spear["y"]), 42, 10)
            hit = False
            for enemy in enemies:
                if enemy.is_alive() and spear_rect.colliderect(pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)):
                    enemy.take_damage(spear["damage"], 1 if spear["vx"] > 0 else -1, is_heavy=True)
                    hit = True
                    break
            if hit or spear["x"] < camera_x - 100 or spear["x"] > camera_x + WIDTH + 100:
                spear_projectiles.remove(spear)

        # Guards and kings fire arrows; a sword swing can parry them.
        for arrow in arrows[:]:
            arrow["x"] += arrow["vx"]
            arrow["y"] += arrow["vy"]
            arrow_rect = pygame.Rect(int(arrow["x"] - 10), int(arrow["y"] - 4), 20, 8)
            if arrow_rect.colliderect(player.get_hitbox()):
                if player.attack_timer <= 0 and player.shield_timer <= 0:
                    player.health -= arrow["damage"]
                arrows.remove(arrow)
            elif arrow["x"] < camera_x - 120 or arrow["x"] > camera_x + WIDTH + 120:
                arrows.remove(arrow)

        if player.health <= 0:
            
            player.lives -= 1
            if player.lives > 0:
                safe_x, safe_y = stage_layout.find_safe_respawn(player.x, player.width, player.height)
                player.x = safe_x
                player.y = safe_y - 15
                player.vel_x = 0
                player.vel_y = 0
                player.knockback_x = 0
                player.health = player.max_health
                player.shield_timer = 300
            else:
                game_progress["arrow_ammo"] = 30
                world.set_stage(current_stage)
                stage_layout = StageLayout(stage=current_stage)
                enemies = create_stage_enemies(current_stage, stage_layout)
                spear_projectiles.clear()
                arrows.clear()
                player.x = 300
                player.y = GROUND_Y - player.height
                player.vel_x = 0
                player.vel_y = 0
                player.knockback_x = 0
                player.health = player.max_health
                player.lives = player.max_lives
                player.shield_timer = 180
                camera_x = 0
                camera_y = 0
                pruned_world_x = 0
                last_prune_camera_x = 0

    king_alive = False
    for enemy in enemies:
        if enemy.enemy_type == "king" and enemy.is_alive():
            king_alive = True
            break
    king_defeated = not king_alive

    if king_defeated and stage_layout.can_enter_gate(player.x) and not stage_reward_claimed:
        complete_stage(game_progress, current_stage)
        add_coins(game_progress, 6)
        stage_reward_claimed = True
        if current_stage < 12:
            current_stage += 1
            world.set_stage(current_stage)
            stage_layout = StageLayout(current_stage)
            enemies = create_stage_enemies(current_stage, stage_layout)
            spear_projectiles.clear()
            arrows.clear()
            player.x = 300
            player.y = GROUND_Y - player.height
            player.vel_x = 0
            player.vel_y = 0
            camera_x = 0
            camera_y = 0
            pruned_world_x = 0
            last_prune_camera_x = 0
            king_defeated = False
            stage_reward_claimed = False

    target_camera_x = (player.x - WIDTH // 2)
    camera_x += (target_camera_x - camera_x) * 0.1
    camera_x = max(pruned_world_x, min(camera_x, max(0, stage_layout.stage_length - WIDTH)))

    # إزالة العالم القديم على دفعات بدلاً من إبقاء آلاف العناصر طوال المرحلة.
    if camera_x - last_prune_camera_x >= 500:
        new_cutoff = max(pruned_world_x, int(camera_x) - 1400)
        if new_cutoff > pruned_world_x:
            pruned_world_x = new_cutoff
            world.prune_behind(pruned_world_x)
            stage_layout.prune_behind(pruned_world_x)
            # الأعداء الأحياء خلف الحد لا يمكن الرجوع إليهم؛ احتفظ بالموتى فقط
            # حتى يكملوا أنيميشن السقوط والاختفاء.
            enemies = [
                enemy for enemy in enemies
                if enemy.x + enemy.width >= pruned_world_x or not enemy.is_alive()
            ]
        last_prune_camera_x = camera_x

    target_camera_y = (player.y + player.height // 2 - HEIGHT // 2)
    camera_y += (target_camera_y - camera_y) * 0.1

    world.draw(screen, camera_x, camera_y)
    stage_layout.draw(screen, camera_x, camera_y)

    draw_min_x = camera_x - DRAW_MARGIN_X
    draw_max_x = camera_x + WIDTH + DRAW_MARGIN_X
    for enemy in enemies:
        if draw_min_x <= enemy.x <= draw_max_x:
            enemy.draw(screen, camera_x, camera_y, WIDTH)

    player.draw(screen)
    draw_legendary_effect(player)
    draw_touch_controls(pressed_buttons)

    font = HUD_FONT
    state_ar = {"idle": "استعداد", "run": "جري", "jump": "قفز", "attack": "هجوم", "special": "مهارة", "legendary": "قاضية", "crouch": "انحناء"}.get(player.state, player.state)
    hud_lines = [
        f"الحالة: {state_ar}" if game_settings.get("language", "ar") == "ar" else f"STATE: {player.state}",
        f"الضربات: {player.combo_step}/4" if game_settings.get("language", "ar") == "ar" else f"COMBO: {player.combo_step}/4",
        f"القفزات: {player.jumps_left}" if game_settings.get("language", "ar") == "ar" else f"JUMPS: {player.jumps_left}",
        f"المرحلة: {current_stage}/12" if game_settings.get("language", "ar") == "ar" else f"STAGE: {current_stage}/12",
        f"الصحة: {int(max(0, player.health))}" if game_settings.get("language", "ar") == "ar" else f"HEALTH: {int(max(0, player.health))}",
    ]
    for idx, line in enumerate(hud_lines):
        color = RED if idx == 4 else (GOLD if idx == 5 else WHITE)
        screen.blit(font.render(fix_text(line), True, color), (20, 20 + idx * 30))

    for i in range(player.max_lives):
        draw_heart_icon(screen, 38 + i * 38, 188, 28, filled=(i < player.lives))

    coins_label = f"العملات: {game_progress['coins']}" if game_settings.get("language", "ar") == "ar" else f"COINS: {game_progress['coins']}"
    screen.blit(font.render(fix_text(coins_label), True, GOLD), (20, 215))
    if game_progress.get("spear_unlocked", False):
        ammo_label = f"السهام: {game_progress.get('arrow_ammo', 0)}" if game_settings.get("language", "ar") == "ar" else f"ARROWS: {game_progress.get('arrow_ammo', 0)}"
        screen.blit(font.render(fix_text(ammo_label), True, GOLD), (20, 305))

    if player.shield_timer > 0:
        sec_left = math.ceil(player.shield_timer / 60.0)
        shield_label = f"الدرع: {sec_left}ث" if game_settings.get("language", "ar") == "ar" else f"SHIELD: {sec_left}s"
        screen.blit(font.render(fix_text(shield_label), True, CYAN), (20, 245))

    for spear in spear_projectiles:
        pygame.draw.line(screen, (210, 190, 140), (int(spear["x"] - camera_x), int(spear["y"] - camera_y)), (int(spear["x"] + 38 - camera_x), int(spear["y"] - camera_y)), 5)
        pygame.draw.polygon(screen, (230, 230, 220), [(int(spear["x"] + 42 - camera_x), int(spear["y"] - camera_y)), (int(spear["x"] + 30 - camera_x), int(spear["y"] - camera_y - 6)), (int(spear["x"] + 30 - camera_x), int(spear["y"] - camera_y + 6))])
    for arrow in arrows:
        ax, ay = int(arrow["x"] - camera_x), int(arrow["y"] - camera_y)
        pygame.draw.line(screen, (120, 75, 35), (ax - 12, ay), (ax + 12, ay), 3)
        pygame.draw.polygon(screen, (210, 210, 210), [(ax + 13, ay), (ax + 5, ay - 5), (ax + 5, ay + 5)])

    draw_skill_buttons()
    if player.legendary_cooldown > 0:
        ready_left = math.ceil(player.legendary_cooldown / FPS)
        ready_label = f"القاضية بعد: {ready_left}ث" if game_settings.get("language", "ar") == "ar" else f"ULTIMATE: {ready_left}s"
    else:
        ready_label = "القاضية جاهزة" if game_settings.get("language", "ar") == "ar" else "ULTIMATE READY"
    screen.blit(font.render(fix_text(ready_label), True, GOLD), (20, 275))
    draw_pause_button_and_overlay(paused, game_settings)

    present(screen)

pygame.quit()
sys.exit()
