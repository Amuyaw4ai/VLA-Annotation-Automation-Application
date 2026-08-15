import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    "global_hotkey": os.getenv("GLOBAL_HOTKEY", "<alt>+<space>"),
    "auto_copy": os.getenv("AUTO_COPY_CLIPBOARD", "true").lower() == "true",
    "play_audio": os.getenv("PLAY_AUDIO_FEEDBACK", "true").lower() == "true",
    "forbidden_words": [
        "operator", "worker", "person", "people",
        "left hand", "right hand", "hand", "hands",
        "arm", "arms", "robotic arm", "human", "someone"
    ],
    "history_limit": 50
}

class Config:
    def __init__(self):
        self.config_data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.config_data.update(saved)
            except Exception as e:
                print(f"[Config] Error loading {CONFIG_FILE}: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4)
        except Exception as e:
            print(f"[Config] Error saving {CONFIG_FILE}: {e}")

    def get(self, key, default=None):
        return self.config_data.get(key, default)

    def set(self, key, value):
        self.config_data[key] = value
        self.save()

config = Config()
