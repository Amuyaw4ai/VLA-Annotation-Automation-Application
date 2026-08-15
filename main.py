import sys
import time
import argparse
from config import config
from clipboard_listener import clipboard_service

def run_headless():
    hotkey = config.get("global_hotkey", "<ctrl>+<space>")
    auto_detect = config.get("auto_detect_clipboard", False)
    print("=" * 65)
    print(" ⚡ VLA Annotation Automation Assistant (Headless Mode) ")
    print("=" * 65)
    print(f" • Global Hotkey Listener: [{hotkey}] ACTIVE")
    print(f" • Autonomous Auto-Snip Mode: {'ENABLED (Auto-detects Win+Shift+S)' if auto_detect else 'DISABLED (Press Ctrl+Space to trigger)'}")
    print(f" • Vision Model: {config.get('gemini_model', 'gemini-flash-latest')}")
    print(f" • Auto-Copy to Clipboard: {'ENABLED' if config.get('auto_copy', True) else 'DISABLED'}")
    print(f" • Audio Chime Feedback: {'ENABLED' if config.get('play_audio', True) else 'DISABLED'}")
    print("-" * 65)
    print(" Workflow instructions:")
    print(" 1. Play video on Annotasks platform.")
    print(" 2. Take a screenshot snip using Win + Shift + S.")
    print(f" 3. Press {hotkey} anywhere on desktop (or let Autonomous Mode process automatically).")
    print(" 4. High-Level Caption is generated & auto-copied to clipboard in <1.5s!")
    print(" 5. Press Ctrl + V into Annotasks text field.")
    print("=" * 65)
    print(" Press Ctrl+C in this terminal window to stop.")
    print()

    def headless_callback(result):
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ [{result.get('timestamp')}] Caption ({result.get('latency_seconds')}s): '{result.get('high_level_caption')}'")
            if not result.get("is_valid"):
                print(f"   ⚠️ Rule Warning: {', '.join(result.get('violations', []))}")

    clipboard_service.callback = headless_callback
    clipboard_service.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping background listener...")
        clipboard_service.stop()
        print("Goodbye!")

def run_gui():
    from gui_app import main as gui_main
    gui_main()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VLA Annotation Automation Assistant")
    parser.add_argument("--headless", action="store_true", help="Run in headless background hotkey listener mode")
    args = parser.parse_args()

    if args.headless:
        run_headless()
    else:
        run_gui()
