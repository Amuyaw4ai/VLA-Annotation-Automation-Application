import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

CONFIG_FILE = Path(__file__).parent / "config.json"

# Non-sensitive default preferences
DEFAULT_CONFIG = {
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
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
    """
    Secure Configuration Manager:
    Enforces Zero-Secrets-in-Code policy by keeping API credentials strictly in memory
    or environment variables. Never persists private keys to disk configuration files.
    """
    def __init__(self):
        self.config_data = DEFAULT_CONFIG.copy()
        # In-memory sensitive credentials store (never written to config.json)
        self._runtime_api_key = os.getenv("GEMINI_API_KEY", "")
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    # Never load API keys from config.json to prevent secret leaks
                    saved.pop("gemini_api_key", None)
                    self.config_data.update(saved)
            except Exception as e:
                print(f"[Config Security] Error loading {CONFIG_FILE}: {e}")

    def save(self):
        """
        Saves non-sensitive configuration to disk. Strips all secret keys.
        """
        try:
            to_save = self.config_data.copy()
            # Guarantee secret fields are omitted from disk files
            to_save.pop("gemini_api_key", None)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(to_save, f, indent=4)
        except Exception as e:
            print(f"[Config Security] Error saving {CONFIG_FILE}: {e}")

    def get_api_key(self) -> str:
        """
        Returns API Key from environment or runtime memory store.
        """
        return os.getenv("GEMINI_API_KEY") or self._runtime_api_key

    def set_api_key(self, api_key: str):
        """
        Sets runtime API Key in memory (does not save to disk).
        """
        self._runtime_api_key = api_key.strip()

    def get(self, key, default=None):
        if key == "gemini_api_key":
            return self.get_api_key()
        return self.config_data.get(key, default)

    def set(self, key, value):
        if key == "gemini_api_key":
            self.set_api_key(value)
        else:
            self.config_data[key] = value
            self.save()

config = Config()
