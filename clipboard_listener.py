import os
import time
import json
import hashlib
import threading
import winsound
import pyperclip
from PIL import ImageGrab, Image
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List

from config import config
from vla_engine import engine

HISTORY_FILE = Path(__file__).parent / "history.json"

class ClipboardListener:
    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.callback = callback
        self.listener = None
        self.is_running = False
        self.history: List[Dict[str, Any]] = self._load_history()
        self._lock = threading.Lock()
        self.last_img_hash = None
        self.active_image: Optional[Image.Image] = None
        self.active_captions: Dict[str, Dict[str, Any]] = {}
        self._poller_thread = None
        self._stop_poller = threading.Event()

    def _load_history(self) -> List[Dict[str, Any]]:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ClipboardListener] Error loading history: {e}")
        return []

    def _save_history(self):
        try:
            limit = config.get("history_limit", 50)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history[:limit], f, indent=2)
        except Exception as e:
            print(f"[ClipboardListener] Error saving history: {e}")

    def add_to_history(self, item: Dict[str, Any]):
        with self._lock:
            self.history.insert(0, item)
            limit = config.get("history_limit", 50)
            self.history = self.history[:limit]
            self._save_history()

    def play_feedback_sound(self, success: bool = True):
        if not config.get("play_audio", True):
            return
        try:
            if success:
                winsound.Beep(1200, 100)
                winsound.Beep(1800, 120)
            else:
                winsound.Beep(400, 250)
        except Exception:
            pass

    def _compute_image_hash(self, img: Image.Image) -> str:
        try:
            return hashlib.md5(img.tobytes()).hexdigest()
        except Exception:
            return str(time.time())

    def reprocess_active_image(self, target_mode: str) -> Optional[Dict[str, Any]]:
        """
        Task 2 Feature: Switches mode and re-processes/retrieves caption for the active image in memory without re-snipping.
        """
        if self.active_image is None:
            return None
        return self.process_clipboard_frame(override_img=self.active_image, mode=target_mode)

    def process_clipboard_frame(self, override_img: Optional[Image.Image] = None, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Task 2 Dual-Caption Single-Snip Memory Cache:
        Grabs image from clipboard/memory, caches captions per mode, and avoids double-snipping.
        """
        current_mode = mode or config.get("annotation_mode", "high_level")
        img = override_img

        if img is None:
            try:
                img = ImageGrab.grabclipboard()
            except Exception as e:
                print(f"[ClipboardListener] Error grabbing clipboard: {e}")

        if img is None or not isinstance(img, Image.Image):
            # Fall back to active image in memory if available
            img = self.active_image

        if img is None or not isinstance(img, Image.Image):
            res = {
                "error": "No image found in clipboard or memory! Use Win + Shift + S to take a screenshot first.",
                "is_valid": False,
                "timestamp": time.strftime("%H:%M:%S")
            }
            self.play_feedback_sound(success=False)
            if self.callback:
                self.callback(res)
            return res

        # Convert to RGB if necessary
        if img.mode != "RGB":
            img = img.convert("RGB")

        new_hash = self._compute_image_hash(img)

        # If a NEW screenshot is taken (hash differs), clear memory cache
        if self.last_img_hash != new_hash:
            self.last_img_hash = new_hash
            self.active_image = img
            self.active_captions = {}

        # Instant Cache Check for current mode
        if current_mode in self.active_captions:
            cached_result = self.active_captions[current_mode]
            print(f"[ClipboardListener Memory Cache] Instant cache hit for mode '{current_mode}' (0.0s latency)!")
            if cached_result.get("is_valid") and cached_result.get("high_level_caption"):
                if config.get("auto_copy", True):
                    try:
                        pyperclip.copy(cached_result["high_level_caption"])
                    except Exception:
                        pass
                self.play_feedback_sound(success=True)

            if self.callback:
                self.callback(cached_result)
            return cached_result

        # Process frame with Gemini VLA engine under current_mode
        start_time = time.time()
        result = engine.analyze_image(img, mode=current_mode)
        elapsed = round(time.time() - start_time, 2)
        result["latency_seconds"] = elapsed
        result["timestamp"] = time.strftime("%H:%M:%S")

        # Cache result in memory for instant mode toggling
        self.active_captions[current_mode] = result

        # Auto-copy caption to system clipboard if successful
        if result.get("is_valid") and result.get("high_level_caption"):
            caption = result["high_level_caption"]
            if config.get("auto_copy", True):
                try:
                    pyperclip.copy(caption)
                    print(f"[ClipboardListener] Caption ({current_mode}) copied in {elapsed}s: '{caption}'")
                except Exception as e:
                    print(f"[ClipboardListener] Pyperclip copy error: {e}")

            self.play_feedback_sound(success=True)
        else:
            self.play_feedback_sound(success=False)

        # Save to history log
        self.add_to_history(result)

        # Trigger callback for GUI update
        if self.callback:
            self.callback(result)

        return result

    def _on_hotkey(self):
        threading.Thread(target=self.process_clipboard_frame, daemon=True).start()

    def _clipboard_poller_loop(self):
        """
        Autonomous Mode: Continuously polls clipboard for new screenshots.
        Triggers automatically when a new screenshot image is detected.
        """
        while not self._stop_poller.is_set():
            time.sleep(0.3)
            if not config.get("auto_detect_clipboard", False):
                continue

            try:
                img = ImageGrab.grabclipboard()
                if img and isinstance(img, Image.Image):
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img_hash = self._compute_image_hash(img)
                    if self.last_img_hash is None or img_hash != self.last_img_hash:
                        print("[ClipboardListener Autonomous] New screenshot detected! Auto-processing...")
                        self.last_img_hash = img_hash
                        self.process_clipboard_frame()
                else:
                    # Clipboard holds text or non-image; reset hash for immediate next snip detection
                    self.last_img_hash = None
            except Exception:
                pass

    def start(self):
        if self.is_running:
            return

        try:
            from pynput import keyboard
            hotkey_str = config.get("global_hotkey", "<ctrl>+<space>")
            print(f"[ClipboardListener] Starting listener bound to hotkey {hotkey_str}")

            hotkeys_dict = {
                hotkey_str: self._on_hotkey
            }

            self.listener = keyboard.GlobalHotKeys(hotkeys_dict)
            self.listener.start()
            self.is_running = True

            # Start autonomous clipboard poller
            self._stop_poller.clear()
            self._poller_thread = threading.Thread(target=self._clipboard_poller_loop, daemon=True)
            self._poller_thread.start()

        except Exception as e:
            print(f"[ClipboardListener] Failed to start global listener: {e}")
            self.is_running = False

    def stop(self):
        self._stop_poller.set()
        if self.listener and self.is_running:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.is_running = False
            print("[ClipboardListener] Listener stopped.")

clipboard_service = ClipboardListener()
