
import pygame
import json
import os
import copy
import math

from world import World
from stage_layout import StageLayout
from game_paths import asset_path, settings_path

# دعم تشكيل وعرض الحروف العربية
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False


SETTINGS_FILE = settings_path()

WHITE = (255, 255, 255)
GOLD = (240, 190, 40)
BG = (20, 25, 35)
PANEL = (30, 38, 55)
BLUE = (50, 135, 210)
GREEN = (45, 160, 90)
RED = (180, 65, 65)

DEFAULT_POSITIONS = {
    "back": (30, 605, 80, 80),
    "forward": (120, 605, 80, 80),
    "down": (75, 505, 80, 80),
    "jump": (900, 605, 80, 80),
    "attack": (990, 605, 80, 80),
    "special": (1080, 505, 80, 80),
    "legendary": (1170, 605, 80, 80),
}

DEFAULT_JOYSTICK = {
    "x": 160,
    "y": 570,
    "radius": 75
}

DEFAULT_OPACITY = {
    "back": 190,
    "forward": 190,
    "down": 190,
    "jump": 190,
    "attack": 210,
    "special": 210,
    "legendary": 210,
    "joystick": 180
}

LABELS = {
    "back": ("<", "LEFT"),
    "forward": (">", "RIGHT"),
    "down": ("v", "CROUCH"),
    "jump": ("^", "JUMP"),
    "attack": ("X", "ATTACK"),
    "special": ("*", "SPECIAL"),
    "legendary": ("!", "ULTIMATE")
}

# الترجمات المستخدمة داخل المحرر
TRANSLATIONS = {
    "BUTTONS": "الأزرار",
    "JOYSTICK": "عصا التحكم",
    "GRID ON": "الشبكة تشغيل",
    "GRID OFF": "الشبكة إيقاف",
    "SNAP ON": "المحاذاة تشغيل",
    "SNAP OFF": "المحاذاة إيقاف",
    "UNDO": "تراجع",
    "REDO": "إعادة",
    "EDIT": "تعديل",
    "PREVIEW": "معاينة",
    "SAVE": "حفظ",
    "DEFAULT": "افتراضي",
    "BACK": "رجوع",

    "STAGE": "المرحلة",
    "CONTROL EDITOR": "تخصيص أزرار التحكم",

    "LEFT": "يسار",
    "RIGHT": "يمين",
    "CROUCH": "انحناء",
    "JUMP": "قفز",
    "ATTACK": "هجوم",
    "SPECIAL": "هجوم خاص",
    "ULTIMATE": "هجوم خارق",

    "NONE": "لا شيء",
    "SELECTED": "المحدد",
    "OPACITY": "الشفافية",
    "Drag the slider to change transparency":
        "اسحب الشريط لتغيير الشفافية",

    "PREVIEW MODE": "وضع المعاينة",

    "Drag buttons to move | Drag yellow corner to resize":
        "اسحب الأزرار لتحريكها واسحب الزاوية الصفراء لتغيير الحجم",

    "Nothing to undo": "لا يوجد شيء للتراجع عنه",
    "Nothing to redo": "لا يوجد شيء لإعادته",
    "Settings saved successfully": "تم حفظ الإعدادات بنجاح",
    "Save failed - check settings file": "فشل الحفظ، تحقق من ملف الإعدادات",
    "Default positions restored - press SAVE":
        "تمت استعادة المواقع الافتراضية، اضغط حفظ",
}


def load_touch_config(settings):
    if not isinstance(settings, dict):
        settings = {}

    config = settings.get("touch_controls")

    if not isinstance(config, dict):
        config = {}

    config.setdefault("mode", "buttons")

    if config["mode"] not in ("buttons", "joystick"):
        config["mode"] = "buttons"

    if not isinstance(config.get("positions"), dict):
        config["positions"] = {}

    if not isinstance(config.get("joystick"), dict):
        config["joystick"] = {}

    if not isinstance(config.get("opacity"), dict):
        config["opacity"] = {}

    for name, value in DEFAULT_OPACITY.items():
        config["opacity"].setdefault(name, value)

    config.setdefault("grid", True)
    config.setdefault("snap", False)

    settings["touch_controls"] = config
    return config


def get_control_rects(settings, width, height):
    config = load_touch_config(settings)
    rects = {}

    for name, default in DEFAULT_POSITIONS.items():
        x, y, w, h = default
        saved = config["positions"].get(name)

        if isinstance(saved, dict):
            x = saved.get("x", x)
            y = saved.get("y", y)
            w = saved.get("w", w)
            h = saved.get("h", h)

        try:
            w = max(45, min(150, int(w)))
            h = max(45, min(150, int(h)))
            x = int(x)
            y = int(y)
        except (ValueError, TypeError):
            x, y, w, h = default

        w = min(w, width)
        h = min(h, height)

        x = max(0, min(x, width - w))
        y = max(0, min(y, height - h))

        rects[name] = pygame.Rect(x, y, w, h)

    return rects


def get_joystick(settings):
    config = load_touch_config(settings)
    saved = config["joystick"]

    try:
        x = int(saved.get("x", DEFAULT_JOYSTICK["x"]))
        y = int(saved.get("y", DEFAULT_JOYSTICK["y"]))
        radius = int(saved.get("radius", DEFAULT_JOYSTICK["radius"]))
    except (ValueError, TypeError):
        return DEFAULT_JOYSTICK.copy()

    return {
        "x": max(40, min(1240, x)),
        "y": max(40, min(680, y)),
        "radius": max(40, min(120, radius))
    }


class ControlEditor:
    def __init__(self, screen, settings, stage=1):
        self.screen = screen
        self.settings = settings
        self.stage = stage

        self.width, self.height = screen.get_size()

        # قراءة لغة اللعبة من الإعدادات نفسها
        language = str(settings.get("language", "ar")).lower()

        if language.startswith("ar") or language in ("arabic", "العربية"):
            self.language = "ar"
        else:
            self.language = "en"

        self.is_arabic = self.language == "ar"

        # استخدام خطوط تدعم العربية على ويندوز
        self.font = self.create_font(23, True)
        self.small_font = self.create_font(16, True)
        self.tiny_font = self.create_font(13, True)

        self.config = load_touch_config(settings)
        self.mode = self.config.get("mode", "buttons")

        self.rects = get_control_rects(
            settings, self.width, self.height
        )

        self.joystick = get_joystick(settings)

        self.opacity = copy.deepcopy(
            self.config.get("opacity", DEFAULT_OPACITY)
        )

        for name, value in DEFAULT_OPACITY.items():
            self.opacity.setdefault(name, value)

        self.grid_enabled = bool(self.config.get("grid", True))
        self.snap_enabled = bool(self.config.get("snap", False))
        self.grid_size = 20

        self.selected = "attack"
        self.dragging = None
        self.drag_offset = (0, 0)
        self.preview = False
        self.status_message = ""
        self.status_timer = 0

        self.history = []
        self.redo_history = []

        self.toolbar = {
            "mode": pygame.Rect(15, 12, 155, 42),
            "grid": pygame.Rect(180, 12, 95, 42),
            "snap": pygame.Rect(285, 12, 95, 42),
            "undo": pygame.Rect(390, 12, 85, 42),
            "redo": pygame.Rect(485, 12, 85, 42),
            "preview": pygame.Rect(580, 12, 100, 42),
            "prev": pygame.Rect(690, 12, 42, 42),
            "next": pygame.Rect(738, 12, 42, 42),
            "save": pygame.Rect(790, 12, 125, 42),
            "reset": pygame.Rect(925, 12, 125, 42),
            "back": pygame.Rect(1060, 12, 125, 42),
        }

        self.opacity_panel = pygame.Rect(15, 75, 270, 125)
        self.opacity_slider = pygame.Rect(35, 163, 225, 10)

        self.slider_dragging = False

        self.world = None
        self.layout = None
        self.load_stage()

    # -------------------------------------------------
    # اللغة والخطوط
    # -------------------------------------------------

    def create_font(self, size, bold=False):
        if self.is_arabic:
            font_paths = [
                asset_path("fonts", "NotoSansArabic-Bold.ttf"),
                asset_path("fonts", "NotoSansArabic-Regular.ttf"),
                "C:/Windows/Fonts/tahoma.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/segoeui.ttf"
            ]

            for path in font_paths:
                if os.path.exists(path):
                    try:
                        font = pygame.font.Font(path, size)
                        font.set_bold(bold)
                        return font
                    except Exception:
                        pass

        return pygame.font.SysFont("arial", size, bold=bold)

    def fix_text(self, text):
        text = str(text)

        if self.is_arabic and ARABIC_SUPPORT:
            try:
                reshaped = arabic_reshaper.reshape(text)
                return get_display(reshaped)
            except Exception:
                return text

        return text

    def render_text(self, text, font, color):
        return font.render(
            self.fix_text(text),
            True,
            color
        )

    def tr(self, text):
        if not self.is_arabic:
            return text

        return TRANSLATIONS.get(text, text)

    def control_label(self, name):
        symbol, english_label = LABELS[name]
        return symbol, self.tr(english_label)

    # -------------------------------------------------
    # تحميل المرحلة
    # -------------------------------------------------

    def load_stage(self):
        try:
            self.world = World(stage=self.stage)
        except Exception:
            self.world = None

        try:
            self.layout = StageLayout(stage=self.stage)
        except Exception:
            self.layout = None

    def snapshot(self):
        return {
            "rects": {
                name: rect.copy()
                for name, rect in self.rects.items()
            },
            "joystick": copy.deepcopy(self.joystick),
            "opacity": copy.deepcopy(self.opacity),
            "mode": self.mode
        }

    def push_history(self):
        self.history.append(self.snapshot())

        if len(self.history) > 60:
            self.history.pop(0)

        self.redo_history.clear()

    def restore_snapshot(self, state):
        self.rects = {
            name: rect.copy()
            for name, rect in state["rects"].items()
        }

        self.joystick = copy.deepcopy(state["joystick"])
        self.opacity = copy.deepcopy(state["opacity"])
        self.mode = state["mode"]

    def undo(self):
        if not self.history:
            self.set_status("Nothing to undo")
            return

        self.redo_history.append(self.snapshot())
        self.restore_snapshot(self.history.pop())

    def redo(self):
        if not self.redo_history:
            self.set_status("Nothing to redo")
            return

        self.history.append(self.snapshot())
        self.restore_snapshot(self.redo_history.pop())

    def set_status(self, message):
        self.status_message = message
        self.status_timer = 150

    # -------------------------------------------------
    # الحفظ والاستعادة
    # -------------------------------------------------

    def save(self):
        self.config["mode"] = self.mode
        self.config["positions"] = {}

        for name, rect in self.rects.items():
            self.config["positions"][name] = {
                "x": rect.x,
                "y": rect.y,
                "w": rect.width,
                "h": rect.height
            }

        self.config["joystick"] = copy.deepcopy(self.joystick)
        self.config["opacity"] = copy.deepcopy(self.opacity)
        self.config["grid"] = self.grid_enabled
        self.config["snap"] = self.snap_enabled

        self.settings["touch_controls"] = self.config

        try:
            folder = os.path.dirname(SETTINGS_FILE)

            if folder:
                os.makedirs(folder, exist_ok=True)

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    self.settings,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            self.set_status("Settings saved successfully")

        except Exception as e:
            print("خطأ في حفظ إعدادات اللمس:", e)
            self.set_status("Save failed - check settings file")

    def reset(self):
        self.push_history()

        self.rects = get_control_rects(
            {"touch_controls": {}},
            self.width,
            self.height
        )

        self.joystick = DEFAULT_JOYSTICK.copy()
        self.opacity = copy.deepcopy(DEFAULT_OPACITY)
        self.mode = "buttons"
        self.selected = "attack"

        self.set_status("Default positions restored - press SAVE")

    def change_stage(self, amount):
        self.stage = max(1, min(12, self.stage + amount))
        self.load_stage()

    # -------------------------------------------------
    # رسم المرحلة
    # -------------------------------------------------

    def draw_stage(self):
        self.screen.fill((90, 145, 190))

        if self.world:
            try:
                self.world.draw(self.screen, 0, 0)
            except Exception:
                pass

        if self.layout:
            try:
                self.layout.draw(self.screen, 0, 0)
            except Exception:
                pass

        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 65))
        self.screen.blit(overlay, (0, 0))

        if self.grid_enabled:
            grid_surface = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA
            )

            for x in range(0, self.width, self.grid_size):
                pygame.draw.line(
                    grid_surface,
                    (255, 255, 255, 35),
                    (x, 60),
                    (x, self.height)
                )

            for y in range(60, self.height, self.grid_size):
                pygame.draw.line(
                    grid_surface,
                    (255, 255, 255, 35),
                    (0, y),
                    (self.width, y)
                )

            self.screen.blit(grid_surface, (0, 0))

    # -------------------------------------------------
    # رسم أزرار الشريط العلوي
    # -------------------------------------------------

    def draw_toolbar_button(self, name, label, color=None):
        rect = self.toolbar[name]

        if color is None:
            color = (45, 60, 80)

        pygame.draw.rect(
            self.screen,
            color,
            rect,
            border_radius=8
        )

        pygame.draw.rect(
            self.screen,
            WHITE,
            rect,
            2,
            border_radius=8
        )

        txt = self.render_text(label, self.small_font, WHITE)
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    # -------------------------------------------------
    # رسم أزرار التحكم
    # -------------------------------------------------

    def draw_button(self, rect, symbol, label, name):
        selected = self.selected == name
        alpha = max(35, min(255, int(self.opacity.get(name, 190))))

        if name in ("special", "legendary"):
            color = (105, 55, 145)
        elif name == "attack":
            color = (165, 65, 55)
        else:
            color = (50, 115, 165)

        surface = pygame.Surface(rect.size, pygame.SRCALPHA)

        pygame.draw.ellipse(
            surface,
            (*color, alpha),
            surface.get_rect()
        )

        pygame.draw.ellipse(
            surface,
            (*WHITE, 255),
            surface.get_rect(),
            3 if selected else 2
        )

        self.screen.blit(surface, rect.topleft)

        text = self.render_text(symbol, self.font, WHITE)

        self.screen.blit(
            text,
            text.get_rect(
                center=(rect.centerx, rect.centery - 8)
            )
        )

        caption = self.render_text(label, self.tiny_font, WHITE)

        self.screen.blit(
            caption,
            caption.get_rect(
                center=(rect.centerx, rect.bottom - 14)
            )
        )

        if selected:
            handle = pygame.Rect(
                rect.right - 12,
                rect.bottom - 12,
                20,
                20
            )

            pygame.draw.rect(
                self.screen,
                GOLD,
                handle,
                border_radius=4
            )

            pygame.draw.rect(
                self.screen,
                WHITE,
                handle,
                2,
                border_radius=4
            )

    # -------------------------------------------------
    # رسم عصا التحكم
    # -------------------------------------------------

    def draw_joystick(self):
        x = int(self.joystick["x"])
        y = int(self.joystick["y"])
        radius = int(self.joystick["radius"])

        alpha = max(
            35,
            min(255, int(self.opacity.get("joystick", 180)))
        )

        surface = pygame.Surface(
            (radius * 2 + 4, radius * 2 + 4),
            pygame.SRCALPHA
        )

        center = (radius + 2, radius + 2)

        pygame.draw.circle(
            surface,
            (50, 60, 75, alpha),
            center,
            radius
        )

        pygame.draw.circle(
            surface,
            (255, 255, 255, 255),
            center,
            radius,
            3
        )

        pygame.draw.circle(
            surface,
            (100, 155, 210, alpha),
            center,
            radius // 2
        )

        pygame.draw.circle(
            surface,
            WHITE,
            center,
            radius // 2,
            2
        )

        self.screen.blit(
            surface,
            (x - radius - 2, y - radius - 2)
        )

        directions = [
            ("↑", x, y - radius + 20),
            ("↓", x, y + radius - 20),
            ("←", x - radius + 20, y),
            ("→", x + radius - 20, y)
        ]

        for symbol, dx, dy in directions:
            txt = self.render_text(symbol, self.font, WHITE)

            self.screen.blit(
                txt,
                txt.get_rect(center=(dx, dy))
            )

        if self.selected == "joystick":
            pygame.draw.circle(
                self.screen,
                GOLD,
                (x + radius, y + radius),
                9
            )

    # -------------------------------------------------
    # لوحة الشفافية
    # -------------------------------------------------

    def draw_opacity_panel(self):
        panel = pygame.Surface(
            self.opacity_panel.size,
            pygame.SRCALPHA
        )

        panel.fill((20, 25, 35, 220))
        self.screen.blit(panel, self.opacity_panel.topleft)

        pygame.draw.rect(
            self.screen,
            WHITE,
            self.opacity_panel,
            2,
            border_radius=10
        )

        if self.selected:
            label = self.selected.upper()
        else:
            label = "NONE"

        selected_text = (
            self.tr("SELECTED") + ": " + self.tr(label)
        )

        title = self.render_text(
            selected_text,
            self.small_font,
            GOLD
        )

        self.screen.blit(title, (30, 88))

        value = int(self.opacity.get(self.selected, 180))
        percent = int(value * 100 / 255)

        opacity_text = (
            self.tr("OPACITY") + ": " + str(percent) + "%"
        )

        txt = self.render_text(
            opacity_text,
            self.small_font,
            WHITE
        )

        self.screen.blit(txt, (30, 120))

        pygame.draw.rect(
            self.screen,
            (70, 80, 95),
            self.opacity_slider,
            border_radius=5
        )

        fill_width = int(
            self.opacity_slider.width * value / 255
        )

        pygame.draw.rect(
            self.screen,
            BLUE,
            (
                self.opacity_slider.x,
                self.opacity_slider.y,
                fill_width,
                self.opacity_slider.height
            ),
            border_radius=5
        )

        knob_x = self.opacity_slider.x + fill_width

        pygame.draw.circle(
            self.screen,
            GOLD,
            (knob_x, self.opacity_slider.centery),
            9
        )

        hint = self.render_text(
            self.tr("Drag the slider to change transparency"),
            self.tiny_font,
            WHITE
        )

        self.screen.blit(hint, (30, 180))

    # -------------------------------------------------
    # رسم الواجهة كاملة
    # -------------------------------------------------

    def draw(self):
        self.draw_stage()

        title_text = (
            self.tr("STAGE") + " " +
            str(self.stage) + " - " +
            self.tr("CONTROL EDITOR")
        )

        title = self.render_text(
            title_text,
            self.font,
            GOLD
        )

        self.screen.blit(
            title,
            title.get_rect(
                center=(self.width // 2, 85)
            )
        )

        self.draw_opacity_panel()

        self.draw_toolbar_button(
            "mode",
            self.tr("BUTTONS")
            if self.mode == "buttons"
            else self.tr("JOYSTICK")
        )

        self.draw_toolbar_button(
            "grid",
            self.tr("GRID ON")
            if self.grid_enabled
            else self.tr("GRID OFF")
        )

        self.draw_toolbar_button(
            "snap",
            self.tr("SNAP ON")
            if self.snap_enabled
            else self.tr("SNAP OFF")
        )

        self.draw_toolbar_button("undo", self.tr("UNDO"))
        self.draw_toolbar_button("redo", self.tr("REDO"))

        self.draw_toolbar_button(
            "preview",
            self.tr("EDIT") if self.preview
            else self.tr("PREVIEW")
        )

        self.draw_toolbar_button("prev", "<")
        self.draw_toolbar_button("next", ">")

        self.draw_toolbar_button(
            "save",
            self.tr("SAVE"),
            GREEN
        )

        self.draw_toolbar_button(
            "reset",
            self.tr("DEFAULT"),
            RED
        )

        self.draw_toolbar_button(
            "back",
            self.tr("BACK")
        )

        if self.mode == "joystick":
            self.draw_joystick()
            visible = ["attack", "special", "legendary"]
        else:
            visible = list(self.rects.keys())

        for name in visible:
            symbol, label = self.control_label(name)

            self.draw_button(
                self.rects[name],
                symbol,
                label,
                name
            )

        if self.preview:
            txt = self.render_text(
                self.tr("PREVIEW MODE"),
                self.font,
                GOLD
            )

            self.screen.blit(
                txt,
                txt.get_rect(
                    center=(self.width // 2, self.height - 30)
                )
            )

        else:
            hint = self.render_text(
                self.tr(
                    "Drag buttons to move | Drag yellow corner to resize"
                ),
                self.small_font,
                WHITE
            )

            self.screen.blit(
                hint,
                hint.get_rect(
                    center=(self.width // 2, self.height - 20)
                )
            )

        if self.status_timer > 0:
            self.status_timer -= 1

            message = self.render_text(
                self.tr(self.status_message),
                self.small_font,
                GOLD
            )

            self.screen.blit(
                message,
                message.get_rect(
                    center=(self.width // 2, 125)
                )
            )

    # -------------------------------------------------
    # التحكم باللمس والماوس
    # -------------------------------------------------

    def visible_names(self):
        if self.mode == "buttons":
            return list(self.rects.keys())

        return ["attack", "special", "legendary"]

    def resize_handle(self, name):
        rect = self.rects[name]

        return pygame.Rect(
            rect.right - 15,
            rect.bottom - 15,
            30,
            30
        )

    def hit_control(self, pos):
        if self.mode == "joystick":
            x = self.joystick["x"]
            y = self.joystick["y"]
            radius = self.joystick["radius"]

            handle_pos = (x + radius, y + radius)

            if math.dist(pos, handle_pos) <= 20:
                return "resize:joystick"

            if math.dist(pos, (x, y)) <= radius:
                return "joystick"

        for name in reversed(self.visible_names()):
            if name == self.selected:
                if self.resize_handle(name).collidepoint(pos):
                    return "resize:" + name

            if self.rects[name].collidepoint(pos):
                return name

        return None

    def snap_value(self, value):
        if not self.snap_enabled:
            return value

        return round(value / self.grid_size) * self.grid_size

    def move_control(self, pos):
        if not self.dragging:
            return

        if self.dragging == "slider":
            self.update_opacity(pos[0])
            return

        if self.dragging == "joystick":
            radius = self.joystick["radius"]

            x = self.snap_value(pos[0] - self.drag_offset[0])
            y = self.snap_value(pos[1] - self.drag_offset[1])

            self.joystick["x"] = max(
                radius,
                min(self.width - radius, x)
            )

            self.joystick["y"] = max(
                radius,
                min(self.height - radius, y)
            )

        elif self.dragging == "resize:joystick":
            x = self.joystick["x"]
            y = self.joystick["y"]

            radius = int(math.dist((x, y), pos))

            self.joystick["radius"] = max(
                40,
                min(120, radius)
            )

        elif self.dragging.startswith("resize:"):
            name = self.dragging.split(":", 1)[1]
            rect = self.rects[name]

            size = max(
                45,
                min(
                    150,
                    max(
                        pos[0] - rect.x,
                        pos[1] - rect.y
                    )
                )
            )

            rect.width = size
            rect.height = size

            rect.right = min(rect.right, self.width)
            rect.bottom = min(rect.bottom, self.height)

        elif self.dragging in self.rects:
            rect = self.rects[self.dragging]

            cx = self.snap_value(
                pos[0] - self.drag_offset[0]
            )

            cy = self.snap_value(
                pos[1] - self.drag_offset[1]
            )

            rect.centerx = max(
                rect.width // 2,
                min(
                    self.width - rect.width // 2,
                    cx
                )
            )

            rect.centery = max(
                rect.height // 2,
                min(
                    self.height - rect.height // 2,
                    cy
                )
            )

    def update_opacity(self, x):
        value = (x - self.opacity_slider.x) / max(
            1,
            self.opacity_slider.width
        )

        value = max(0, min(1, value))
        self.opacity[self.selected] = int(value * 255)

    # -------------------------------------------------
    # التعامل مع ضغط الأزرار
    # -------------------------------------------------

    def start_pointer(self, pos):
        for name, rect in self.toolbar.items():
            if not rect.collidepoint(pos):
                continue

            if name == "back":
                self.save_and_exit = True
                return "back"

            if name == "save":
                self.save()
                return None

            if name == "reset":
                self.reset()
                return None

            if name == "mode":
                self.push_history()

                self.mode = (
                    "joystick"
                    if self.mode == "buttons"
                    else "buttons"
                )

                self.selected = (
                    "joystick"
                    if self.mode == "joystick"
                    else "attack"
                )

                return None

            if name == "grid":
                self.grid_enabled = not self.grid_enabled
                return None

            if name == "snap":
                self.snap_enabled = not self.snap_enabled
                return None

            if name == "undo":
                self.undo()
                return None

            if name == "redo":
                self.redo()
                return None

            if name == "preview":
                self.preview = not self.preview
                return None

            if name == "prev":
                self.change_stage(-1)
                return None

            if name == "next":
                self.change_stage(1)
                return None

        if self.preview:
            return None

        if self.opacity_slider.inflate(10, 25).collidepoint(pos):
            self.push_history()
            self.slider_dragging = True
            self.dragging = "slider"
            self.update_opacity(pos[0])
            return None

        target = self.hit_control(pos)

        if target:
            self.push_history()

            if target.startswith("resize:"):
                self.dragging = target
                name = target.split(":", 1)[1]

                if name == "joystick":
                    self.selected = "joystick"
                else:
                    self.selected = name

                return None

            self.dragging = target

            if target == "joystick":
                self.selected = "joystick"

                self.drag_offset = (
                    pos[0] - self.joystick["x"],
                    pos[1] - self.joystick["y"]
                )

            else:
                self.selected = target
                rect = self.rects[target]

                self.drag_offset = (
                    pos[0] - rect.centerx,
                    pos[1] - rect.centery
                )

        return None

    # -------------------------------------------------
    # الحلقة الرئيسية
    # -------------------------------------------------

    def run(self):
        clock = pygame.time.Clock()

        while True:
            self.draw()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return

                    if event.key == pygame.K_z and (
                        pygame.key.get_mods() & pygame.KMOD_CTRL
                    ):
                        self.undo()

                    if event.key == pygame.K_y and (
                        pygame.key.get_mods() & pygame.KMOD_CTRL
                    ):
                        self.redo()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    result = self.start_pointer(event.pos)

                    if result == "back":
                        return

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        self.move_control(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging = None
                    self.slider_dragging = False

                elif event.type == pygame.FINGERDOWN:
                    pos = (
                        int(event.x * self.width),
                        int(event.y * self.height)
                    )

                    result = self.start_pointer(pos)

                    if result == "back":
                        return

                elif event.type == pygame.FINGERMOTION:
                    if self.dragging:
                        pos = (
                            int(event.x * self.width),
                            int(event.y * self.height)
                        )

                        self.move_control(pos)

                elif event.type == pygame.FINGERUP:
                    self.dragging = None
                    self.slider_dragging = False

            pygame.display.flip()
            clock.tick(60)
