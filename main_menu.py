import pygame
import sys
import json
import os
import copy
import sys

try:
    import arabic_reshaper
    try:
        from bidi.algorithm import get_display
    except ImportError:
        from bidi import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False

from control_editor import ControlEditor
from game_paths import asset_path, bundled_settings_path, settings_path
from progression import load_progress, save_progress
from display_utils import present

LOGICAL_WIDTH = 1280
LOGICAL_HEIGHT = 720

WHITE = (255, 255, 255)
DARK_GRAY = (40, 45, 60)
BLUE_HOVER = (70, 130, 255)
ACTIVE_WAIT = (200, 80, 40)
GOLD = (240, 190, 40)
BG_COLOR = (20, 25, 35)
GREEN = (50, 180, 80)

SETTINGS_FILE = settings_path()
BUNDLED_SETTINGS_FILE = bundled_settings_path()
IS_ANDROID = (sys.platform == "android" or "ANDROID_ARGUMENT" in os.environ)

DEFAULT_SETTINGS = {
    "language": "ar",
    "sound": True,
    "music": True,
    "keys": {
        "left": pygame.K_a,
        "right": pygame.K_d,
        "jump": pygame.K_SPACE,
        "attack": pygame.K_j,
        "special": pygame.K_k,
        "legendary": pygame.K_l,
        "horse": pygame.K_e
    },
    "touch_controls": {
        "mode": "buttons",
        "positions": {},
        "joystick": {
            "x": 160,
            "y": 570,
            "radius": 75
        },
        "opacity": {},
        "grid": True,
        "snap": False
    }
}


def fix_text(text):
    text = str(text)

    if not text or not ARABIC_SUPPORT:
        return text

    # منع إعادة معالجة النص المشكّل
    if any("\uFE70" <= c <= "\uFEFF" for c in text):
        return text

    if not any("\u0600" <= c <= "\u06FF" for c in text):
        return text

    try:
        reshaped = arabic_reshaper.reshape(text)
        try:
            return get_display(reshaped, base_dir="R")
        except TypeError:
            return get_display(reshaped)
    except Exception as e:
        print("Arabic shaping error:", e)
        return text

def get_arabic_font(size):
    font_paths = [
        asset_path("fonts", "NotoSansArabic-Regular.ttf"),
        asset_path("fonts", "NotoSansArabic-Bold.ttf"),
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf"
    ]

    for path in font_paths:
        if os.path.exists(path):
            font = pygame.font.Font(path, size)
            if "Bold" in path:
                font.set_bold(True)
            return font

    return pygame.font.SysFont("tahoma", size, bold=True)


def load_settings():
    data = {}

    settings_source = (
        SETTINGS_FILE
        if os.path.exists(SETTINGS_FILE)
        else BUNDLED_SETTINGS_FILE
    )

    if os.path.exists(settings_source):
        try:
            with open(settings_source, "r", encoding="utf-8-sig") as f:
                loaded = json.load(f)

            if isinstance(loaded, dict):
                data = loaded

        except Exception as e:
            print("تعذر قراءة الإعدادات:", e)

    defaults = copy.deepcopy(DEFAULT_SETTINGS)

    for key, value in defaults.items():
        if key not in data:
            data[key] = value

    if not isinstance(data.get("keys"), dict):
        data["keys"] = {}

    for key, value in DEFAULT_SETTINGS["keys"].items():
        data["keys"].setdefault(key, value)

    if not isinstance(data.get("touch_controls"), dict):
        data["touch_controls"] = {}

    touch_defaults = DEFAULT_SETTINGS["touch_controls"]

    for key, value in touch_defaults.items():
        if key not in data["touch_controls"]:
            data["touch_controls"][key] = copy.deepcopy(value)

    touch = data["touch_controls"]

    if not isinstance(touch.get("positions"), dict):
        touch["positions"] = {}

    if not isinstance(touch.get("joystick"), dict):
        touch["joystick"] = copy.deepcopy(
            touch_defaults["joystick"]
        )

    if not isinstance(touch.get("opacity"), dict):
        touch["opacity"] = {}

    touch.setdefault("grid", True)
    touch.setdefault("snap", False)

    if touch.get("mode") not in ("buttons", "joystick"):
        touch["mode"] = "buttons"

    return data


def save_settings(settings):
    try:
        folder = os.path.dirname(SETTINGS_FILE)

        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                settings,
                f,
                indent=4,
                ensure_ascii=False
            )

    except Exception as e:
        print("خطأ في حفظ الإعدادات:", e)


class Button:
    def __init__(self, x, y, width, height, text, color=DARK_GRAY):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color

    def draw(self, surface, font, active=False):
        mouse_pos = pygame.mouse.get_pos()

        if active:
            draw_col = ACTIVE_WAIT
        elif self.rect.collidepoint(mouse_pos):
            draw_col = BLUE_HOVER
        else:
            draw_col = self.color

        pygame.draw.rect(
            surface,
            draw_col,
            self.rect,
            border_radius=12
        )

        pygame.draw.rect(
            surface,
            WHITE,
            self.rect,
            2,
            border_radius=12
        )

        text_surf = font.render(
            fix_text(self.text),
            True,
            WHITE
        )

        text_rect = text_surf.get_rect(
            center=self.rect.center
        )

        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if not IS_ANDROID and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)

        # Android may deliver native touch events without mouse emulation.
        if event.type == pygame.FINGERDOWN:
            pos = (int(event.x * LOGICAL_WIDTH), int(event.y * LOGICAL_HEIGHT))
            return self.rect.collidepoint(pos)

        return False


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = get_arabic_font(28)
        self.small_font = get_arabic_font(22)
        self.title_font = get_arabic_font(52)

        self.settings = load_settings()
        self.state = "main"
        self.progress = load_progress()
        self.selected_stage = 1
        self.waiting_for_key = None

        self.setup_buttons()

    def t(self, ar_text, en_text):
        return (
            ar_text
            if self.settings.get("language", "ar") == "ar"
            else en_text
        )

    def setup_buttons(self):
        cx = self.screen.get_width() // 2
        h = self.screen.get_height()

        self.btn_start = Button(
            cx - 220, 240, 440, 65, ""
        )

        self.btn_character = Button(
            cx - 220, 330, 440, 65, ""
        )

        self.btn_settings = Button(
            cx - 220, 420, 440, 65, ""
        )

        self.btn_back = Button(
            50, h - 95, 220, 58, ""
        )

        self.btn_play_stage = Button(
            self.screen.get_width() - 270,
            h - 95,
            220,
            58,
            "",
            GREEN
        )

        self.armory_buttons = {
            "sword": Button(cx - 280, 175, 560, 55, ""),
            "shield": Button(cx - 280, 245, 560, 55, ""),
            "spear": Button(cx - 280, 315, 560, 55, ""),
            "jump": Button(cx - 280, 385, 560, 55, ""),
            "berserk": Button(cx - 280, 455, 560, 55, ""),
        }
        self.btn_armory_back = Button(50, h - 95, 220, 58, "")

        self.btn_prev = Button(
            cx - 160, 330, 60, 60, "<"
        )

        self.btn_next = Button(
            cx + 100, 330, 60, 60, ">"
        )

        self.btn_lang = Button(
            cx - 220, 200, 440, 60, ""
        )

        self.btn_sound = Button(
            cx - 220, 280, 440, 60, ""
        )

        self.btn_music = Button(
            cx - 220, 360, 440, 60, ""
        )

        self.btn_controls = Button(
            cx - 220, 440, 440, 60, ""
        )

        self.btn_touch_editor = Button(
            cx - 220, 510, 440, 60, ""
        )

        self.btn_settings_back = Button(
            50, h - 95, 220, 58, ""
        )

        self.key_buttons = {}

        actions = [
            ("left", 160, cx - 320),
            ("right", 230, cx - 320),
            ("jump", 300, cx - 320),
            ("horse", 370, cx - 320),
            ("attack", 160, cx + 20),
            ("special", 230, cx + 20),
            ("legendary", 300, cx + 20)
        ]

        for act, y_pos, x_pos in actions:
            self.key_buttons[act] = Button(
                x_pos,
                y_pos,
                300,
                52,
                ""
            )

        self.btn_reset_keys = Button(
            cx + 20, 370, 300, 52, ""
        )

        self.btn_controls_back = Button(
            50, h - 95, 220, 58, ""
        )

    def update_texts(self):
        self.btn_start.text = self.t(
            "بدأ اللعبة",
            "Start Game"
        )

        self.btn_character.text = self.t(
            "السلاح والشخصية",
            "Weapon & Character"
        )

        self.btn_settings.text = self.t(
            "الإعدادات",
            "Settings"
        )

        self.btn_back.text = self.t("عودة", "Back")

        self.btn_play_stage.text = self.t(
            "ابدأ اللعبة",
            "Play Game"
        )
        self.btn_armory_back.text = self.t("عودة", "Back")

        self.btn_settings_back.text = self.t(
            "حفظ وعودة",
            "Save & Back"
        )

        self.btn_controls_back.text = self.t(
            "عودة للإعدادات",
            "Back to Settings"
        )

        lang_name = (
            "العربية"
            if self.settings["language"] == "ar"
            else "English"
        )

        self.btn_lang.text = self.t(
            f"اللغة: {lang_name}",
            f"Language: {lang_name}"
        )

        snd_stat = self.t(
            "مفعل" if self.settings["sound"] else "معطل",
            "ON" if self.settings["sound"] else "OFF"
        )

        self.btn_sound.text = self.t(
            f"المؤثرات الصوتية: {snd_stat}",
            f"Sound Effects: {snd_stat}"
        )

        mus_stat = self.t(
            "مفعل (قريباً)" if self.settings["music"] else "معطل",
            "ON (Soon)" if self.settings["music"] else "OFF"
        )

        self.btn_music.text = self.t(
            f"الموسيقى: {mus_stat}",
            f"Music: {mus_stat}"
        )

        self.btn_controls.text = self.t(
            "تخصيص أزرار التحكم",
            "Customize Keyboard Controls"
        )

        self.btn_touch_editor.text = self.t(
            "تخصيص أماكن الهجوم",
            "Customize Touch Controls"
        )

        self.btn_reset_keys.text = self.t(
            "استعادة الافتراضي",
            "Reset Defaults"
        )

        labels = {
            "left": ("تحرك يسار", "Move Left"),
            "right": ("تحرك يمين", "Move Right"),
            "jump": ("قفز", "Jump"),
            "attack": ("هجوم عادي", "Normal Attack"),
            "special": ("هجوم خاص", "Special Attack"),
            "legendary": ("الضربة القاضية", "Legendary Attack"),
            "horse": ("ركوب الحصان", "Mount Horse")
        }

        for act, btn in self.key_buttons.items():
            ar_lbl, en_lbl = labels[act]
            lbl = self.t(ar_lbl, en_lbl)

            if self.waiting_for_key == act:
                key_name = self.t(
                    "اضغط زراً...",
                    "Press key..."
                )
            else:
                key_name = pygame.key.name(
                    self.settings["keys"][act]
                ).upper()

            btn.text = f"{lbl} : [ {key_name} ]"

    def open_touch_editor(self):
        try:
            editor = ControlEditor(
                self.screen,
                self.settings,
                self.selected_stage
            )

            editor.run()

            self.settings = load_settings()

        except SystemExit:
            raise

        except Exception as e:
            print("خطأ في محرر أزرار اللمس:", e)

    def run(self):
        clock = pygame.time.Clock()

        while True:
            self.screen.fill(BG_COLOR)
            self.update_texts()

            cx = self.screen.get_width() // 2

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.waiting_for_key is not None:
                    if event.type == pygame.KEYDOWN:
                        if event.key not in (
                            pygame.K_ESCAPE,
                            pygame.K_RETURN
                        ):
                            self.settings["keys"][
                                self.waiting_for_key
                            ] = event.key

                            save_settings(self.settings)

                        self.waiting_for_key = None

                    continue

                if self.state == "main":
                    if self.btn_start.is_clicked(event):
                        self.state = "stage_select"

                    elif self.btn_character.is_clicked(event):
                        self.progress = load_progress()
                        self.state = "armory"

                    elif self.btn_settings.is_clicked(event):
                        self.state = "settings"

                elif self.state == "stage_select":
                    if self.btn_back.is_clicked(event):
                        self.state = "main"

                    elif self.btn_play_stage.is_clicked(event):
                        self.progress = load_progress()
                        if self.selected_stage <= self.progress["unlocked_stage"]:
                            return self.selected_stage

                    elif (
                        self.btn_prev.is_clicked(event)
                        and self.selected_stage > 1
                    ):
                        self.selected_stage -= 1

                    elif (
                        self.btn_next.is_clicked(event)
                        and self.selected_stage < 12
                    ):
                        self.selected_stage += 1

                elif self.state == "armory":
                    if self.btn_armory_back.is_clicked(event):
                        self.state = "main"
                    else:
                        costs = {
                            "sword": 250 + self.progress["sword_level"] * 100,
                            "shield": (5000, 6000, 7000, 8000, 9000)[min(4, int(self.progress.get("shield_level", 0)))],
                            "spear": 3000 if not self.progress["spear_unlocked"] else 1000,
                            "jump": 6000 + self.progress["extra_jump_level"] * 1000,
                            "berserk": 1500 + self.progress["berserk_level"] * 500,
                        }
                        for skill, btn in self.armory_buttons.items():
                            if btn.is_clicked(event):
                                if skill == "shield" and int(self.progress.get("shield_level", 0)) >= 5:
                                    break
                                if skill == "jump" and self.progress["extra_jump_level"] >= 3:
                                    break
                                if skill == "berserk" and self.progress["berserk_level"] >= 3:
                                    break
                                cost = costs[skill]
                                if self.progress["coins"] >= cost:
                                    self.progress["coins"] -= cost
                                    if skill == "sword":
                                        self.progress["sword_level"] += 1
                                    elif skill == "shield":
                                        self.progress["shield_unlocked"] = True
                                        self.progress["shield_level"] = min(5, int(self.progress.get("shield_level", 0)) + 1)
                                    elif skill == "spear":
                                        if not self.progress["spear_unlocked"]:
                                            self.progress["spear_unlocked"] = True
                                            self.progress["arrow_ammo"] = 30
                                            self.progress["arrow_level"] = 0
                                        else:
                                            current_arrow_level = int(self.progress.get("arrow_level", 0))
                                            if current_arrow_level == 0:
                                                self.progress["arrow_ammo"] = 100
                                            else:
                                                self.progress["arrow_ammo"] = int(self.progress.get("arrow_ammo", 0)) + 100
                                            self.progress["arrow_level"] = current_arrow_level + 1
                                    elif skill == "jump":
                                        self.progress["extra_jump_level"] = min(3, self.progress["extra_jump_level"] + 1)
                                    elif skill == "berserk":
                                        self.progress["berserk_level"] = min(3, self.progress["berserk_level"] + 1)
                                    save_progress(self.progress)
                                break

                elif self.state == "settings":
                    if self.btn_settings_back.is_clicked(event):
                        save_settings(self.settings)
                        self.state = "main"

                    elif self.btn_lang.is_clicked(event):
                        self.settings["language"] = (
                            "en"
                            if self.settings["language"] == "ar"
                            else "ar"
                        )

                        save_settings(self.settings)

                    elif self.btn_sound.is_clicked(event):
                        self.settings["sound"] = not self.settings["sound"]
                        save_settings(self.settings)

                    elif self.btn_music.is_clicked(event):
                        self.settings["music"] = not self.settings["music"]
                        save_settings(self.settings)

                    elif self.btn_controls.is_clicked(event):
                        self.state = "controls"

                    elif self.btn_touch_editor.is_clicked(event):
                        self.open_touch_editor()

                elif self.state == "controls":
                    if self.btn_controls_back.is_clicked(event):
                        self.waiting_for_key = None
                        self.state = "settings"

                    elif self.btn_reset_keys.is_clicked(event):
                        self.settings["keys"] = copy.deepcopy(
                            DEFAULT_SETTINGS["keys"]
                        )

                        save_settings(self.settings)

                    else:
                        for act, btn in self.key_buttons.items():
                            if btn.is_clicked(event):
                                self.waiting_for_key = act

            if self.state == "main":
                title = self.title_font.render(
                    "SEF - The Adventurer",
                    True,
                    GOLD
                )

                self.screen.blit(
                    title,
                    title.get_rect(center=(cx, 110))
                )

                self.btn_start.draw(self.screen, self.font)
                self.btn_character.draw(self.screen, self.font)
                self.btn_settings.draw(self.screen, self.font)

            elif self.state == "stage_select":
                title_txt = fix_text(
                    self.t("اختر المرحلة", "Select Stage")
                )

                title = self.title_font.render(
                    title_txt,
                    True,
                    WHITE
                )

                self.screen.blit(
                    title,
                    title.get_rect(center=(cx, 110))
                )

                self.progress = load_progress()
                self.btn_prev.draw(self.screen, self.font)
                self.btn_next.draw(self.screen, self.font, active=(self.selected_stage >= self.progress["unlocked_stage"]))

                stg_lbl = fix_text(
                    self.t(
                        f"المرحلة {self.selected_stage}",
                        f"Stage {self.selected_stage}"
                    )
                )

                stage_text = self.title_font.render(
                    stg_lbl,
                    True,
                    GOLD
                )

                self.screen.blit(
                    stage_text,
                    stage_text.get_rect(center=(cx, 360))
                )
                lock_txt = self.t(
                    f"العملات: {self.progress['coins']}  |  مفتوح حتى: {self.progress['unlocked_stage']}",
                    f"Coins: {self.progress['coins']}  |  Unlocked: {self.progress['unlocked_stage']}"
                )
                lock_surface = self.small_font.render(fix_text(lock_txt), True, GOLD)
                self.screen.blit(lock_surface, lock_surface.get_rect(center=(cx, 430)))
                if self.selected_stage > self.progress["unlocked_stage"]:
                    locked = self.small_font.render(fix_text(self.t("هذه المرحلة مقفلة", "This stage is locked")), True, (255, 100, 100))
                    self.screen.blit(locked, locked.get_rect(center=(cx, 475)))

                self.btn_back.draw(self.screen, self.font)
                self.btn_play_stage.draw(self.screen, self.font, active=(self.selected_stage > self.progress["unlocked_stage"]))

            elif self.state == "armory":
                self.progress = load_progress()
                title_txt = fix_text(self.t("ترسانة البطل والمهارات", "Hero Armory & Skills"))
                title = self.title_font.render(title_txt, True, GOLD)
                self.screen.blit(title, title.get_rect(center=(cx, 85)))
                coin_txt = self.t(f"رصيدك: {self.progress['coins']} عملة", f"Balance: {self.progress['coins']} coins")
                coin_surface = self.font.render(fix_text(coin_txt), True, GOLD)
                self.screen.blit(coin_surface, coin_surface.get_rect(center=(cx, 135)))
                costs = {
                    "sword": 250 + self.progress["sword_level"] * 100,
                    "shield": (5000, 6000, 7000, 8000, 9000)[min(4, int(self.progress.get("shield_level", 0)))],
                    "spear": 3000 if not self.progress["spear_unlocked"] else 1000,
                    "jump": 6000 + self.progress["extra_jump_level"] * 1000,
                    "berserk": 1500 + self.progress["berserk_level"] * 500,
                }
                labels = {
                    "sword": self.t(f"تطوير قوة السيف - المستوى {self.progress['sword_level']} | {costs['sword']} عملة", f"Sword damage level {self.progress['sword_level']} | {costs['sword']} coins"),
                    "shield": self.t(
                        (f"تطوير الدرع: {10 + int(self.progress.get('shield_level', 0)) * 10} ثانية | المستوى الأقصى" if int(self.progress.get("shield_level", 0)) >= 5 else f"تطوير الدرع إلى {20 + int(self.progress.get('shield_level', 0)) * 10} ثانية | {costs['shield']} عملة")
                        if self.progress["shield_unlocked"] else f"فتح الدرع لمدة 20 ثانية | {costs['shield']} عملة",
                        (f"Shield: {10 + int(self.progress.get('shield_level', 0)) * 10}s | MAX LEVEL" if int(self.progress.get("shield_level", 0)) >= 5 else f"Upgrade shield to {20 + int(self.progress.get('shield_level', 0)) * 10}s | {costs['shield']} coins")
                        if self.progress["shield_unlocked"] else f"Unlock 20-second shield | {costs['shield']} coins"
                    ),
                    "spear": self.t(
                        (f"تطوير السهام إلى 100 سهم | {costs['spear']} عملة" if int(self.progress.get("arrow_level", 0)) == 0 else f"تطوير السهام +100 | المخزون: {self.progress.get('arrow_ammo', 0)} | {costs['spear']} عملة")
                        if self.progress['spear_unlocked'] else f"شراء 30 سهماً | {costs['spear']} عملة",
                        (f"Upgrade arrows to 100 | {costs['spear']} coins" if int(self.progress.get("arrow_level", 0)) == 0 else f"Upgrade arrows +100 | Ammo: {self.progress.get('arrow_ammo', 0)} | {costs['spear']} coins")
                        if self.progress['spear_unlocked'] else f"Buy 30 arrows | {costs['spear']} coins"
                    ),
                    "jump": self.t(f"قفزة إضافية - المستوى {self.progress['extra_jump_level']} | {costs['jump']} عملة", f"Extra jump level {self.progress['extra_jump_level']} | {costs['jump']} coins"),
                    "berserk": self.t(f"قوة الغضب - المستوى {self.progress['berserk_level']} | {costs['berserk']} عملة", f"Berserk damage level {self.progress['berserk_level']} | {costs['berserk']} coins"),
                }
                for skill, btn in self.armory_buttons.items():
                    btn.text = labels[skill]
                    btn.draw(self.screen, self.small_font)
                self.btn_armory_back.draw(self.screen, self.font)

            elif self.state == "settings":
                title_txt = fix_text(
                    self.t("الإعدادات", "Settings")
                )

                title = self.title_font.render(
                    title_txt,
                    True,
                    GOLD
                )

                self.screen.blit(
                    title,
                    title.get_rect(center=(cx, 100))
                )

                self.btn_lang.draw(self.screen, self.font)
                self.btn_sound.draw(self.screen, self.font)
                self.btn_music.draw(self.screen, self.font)
                self.btn_controls.draw(self.screen, self.font)
                self.btn_touch_editor.draw(self.screen, self.font)
                self.btn_settings_back.draw(self.screen, self.font)

            elif self.state == "controls":
                title_txt = fix_text(
                    self.t(
                        "تخصيص أزرار التحكم",
                        "Customize Controls"
                    )
                )

                title = self.title_font.render(
                    title_txt,
                    True,
                    GOLD
                )

                self.screen.blit(
                    title,
                    title.get_rect(center=(cx, 80))
                )

                hint_txt = fix_text(
                    self.t(
                        "اضغط على الحركة ثم اضغط الزر الجديد من الكيبورد",
                        "Click an action then press the new key"
                    )
                )

                hint = self.small_font.render(
                    hint_txt,
                    True,
                    WHITE
                )

                self.screen.blit(
                    hint,
                    hint.get_rect(center=(cx, 130))
                )

                for act, btn in self.key_buttons.items():
                    btn.draw(
                        self.screen,
                        self.small_font,
                        active=(self.waiting_for_key == act)
                    )

                self.btn_reset_keys.draw(
                    self.screen,
                    self.small_font
                )

                self.btn_controls_back.draw(
                    self.screen,
                    self.font
                )

            present(self.screen)
            clock.tick(60)
