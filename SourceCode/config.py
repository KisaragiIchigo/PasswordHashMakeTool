import os, json
from typing import Any

APP_NAME = "PasswordHashTool"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}")
CONFIG_PATH = os.path.join(CONFIG_DIR, f"{APP_NAME}.config.json")

DEFAULT_CONFIG = {
    "window": {"w": 560, "h": 380, "x": None, "y": None},
}

def load_config() -> dict:
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict) -> bool:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
