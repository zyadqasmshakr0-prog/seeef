"""Cross-platform paths for desktop and Android builds."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def asset_path(*parts):
    """Return an absolute path to a bundled game asset."""
    return os.path.join(BASE_DIR, "assets", *parts)


def bundled_settings_path():
    return os.path.join(BASE_DIR, "settings.json")


def settings_path():
    """Return a writable per-app settings location on Android and desktop."""
    try:
        import pygame
        folder = pygame.system.get_pref_path("org.sef", "sefadventurer")
    except Exception:
        folder = os.path.join(
            os.path.expanduser("~"),
            ".sef_adventurer"
        )

    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        folder = BASE_DIR

    return os.path.join(folder, "settings.json")
