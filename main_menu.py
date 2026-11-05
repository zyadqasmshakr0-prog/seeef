import pygame
import sys
import json
import os
import copy
import sys

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False

from control_editor import ControlEditor
from game_paths import asset_path, bundled_settings_path, settings_path

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
    if not ARABIC_SUPPORT:
        return text

    if any("\u0600" <= c <= "\u06FF" for c in text):
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)

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
            return pygame.font.Font(path, size)

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
            surface = pygame.display.get_surface()
            if surface is None:
                return False
            width, height = surface.get_size()
            pos = (int(event.x * width), int(event.y * height))
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
            "بدأ اللعبة",
            "Play Game"
        )

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
                        print(">> السلاح والشخصية - قريباً")

                    elif self.btn_settings.is_clicked(event):
                        self.state = "settings"

                elif self.state == "stage_select":
                    if self.btn_back.is_clicked(event):
                        self.state = "main"

                    elif self.btn_play_stage.is_clicked(event):
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

                self.btn_prev.draw(self.screen, self.font)
                self.btn_next.draw(self.screen, self.font)

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

                self.btn_back.draw(self.screen, self.font)
                self.btn_play_stage.draw(self.screen, self.font)

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

            pygame.display.flip()
            clock.tick(60)
