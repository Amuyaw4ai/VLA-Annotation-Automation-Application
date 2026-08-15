# VLA Annotation Automation Application

A high-performance automation suite designed for **Annotasks** to reduce video captioning and task segmentation time to **under 1.5 seconds** per snippet. Built-in linguistic filters automatically adhere to strict client guidelines while ensuring 100% compliance with OAG (Object-Action-Goal) formatting and quality requirements.

---

## 🚀 Key Features

* **Global Hotkey Trigger (`Ctrl + Space`)**: Trigger caption generation from anywhere on your desktop without conflicting with PowerToys (`Alt + Space`).
* **Autonomous Auto-Snip Mode**: Option to auto-detect new screenshots immediately upon taking a snip (`Win + Shift + S`) without needing any hotkey trigger.
* **Manual / On-Demand Protection**: Keep Autonomous Mode disabled to process only when `Ctrl + Space` is pressed, saving API costs on unrelated screenshots.
* **Direct System Clipboard Reading**: Reads image bytes directly from Windows Clipboard (`Win + Shift + S`) with zero file-system latency.
* **Gemini Vision Engine (`gemini-flash-latest`)**: Structured JSON schema output powered by Google GenAI.
* **Strict Quality Guardrails & Auto-Sanitization**: Automatically detects and strips forbidden words (`operator`, `worker`, `person`, `left hand`, `right hand`, `arms`, `robotic arms`) and verifies simple present tense.
* **Instant Clipboard Auto-Copy**: Automatically copies sanitized High-Level Captions to system clipboard for immediate `Ctrl + V` pasting into Annotasks.
* **Audio Feedback & Toast**: Subtle audio chime confirms successful caption generation and clipboard sync.
* **Modern Desktop GUI & History Log**: Real-time preview dashboard, OAG breakdown cards, rule status indicators, and searchable session logs.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
* Python 3.10+ installed on Windows.
* A Gemini API key from [Google AI Studio](https://aistudio.google.com/).

### 2. Install Dependencies
Open PowerShell or Command Prompt in the repository folder:

```bash
pip install -r requirements.txt
```

### 3. Configure API Key & Mode
Create a `.env` file from `.env.example` or enter your API key directly in the Desktop GUI Settings tab:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
GLOBAL_HOTKEY=<ctrl>+<space>
AUTO_DETECT_CLIPBOARD=false
AUTO_COPY_CLIPBOARD=true
PLAY_AUDIO_FEEDBACK=true
```

---

## ⚡ Rapid Annotation Workflow (< 4 min / task)

1. Open Annotasks (`https://app.annotasks.com/`) in your browser.
2. Launch the VLA Assistant:
   ```bash
   python main.py
   ```
   *(Or run in headless background mode using `python main.py --headless`)*
3. **Annotate at High Speed**:
   * **Step 1:** Preview the video at 8x (`Shift + Up Arrow`).
   * **Step 2:** Snip a video frame: press `Win + Shift + S` and drag over the workspace/object.
   * **Step 3:** Press `Ctrl + Space` anywhere on desktop (or enable Autonomous Auto-Snip in Settings).
   * **Step 4:** Listen for the success chime (~1.2s latency). High-Level Caption is automatically copied to your clipboard!
   * **Step 5:** Press `Ctrl + V` into Annotasks and proceed with timeline segmentation (`C` shortcut).

---

## ⌨️ Annotasks & Application Shortcut Reference

| Shortcut | Context | Action / Function |
| :--- | :--- | :--- |
| **`Win + Shift + S`** | Windows | Take screenshot snip of video frame |
| **`Ctrl + Space`** | Global | Process clipboard frame & auto-copy VLA caption |
| **`Ctrl + V`** | Annotasks | Paste High-Level Caption into task |
| **`Shift + Up Arrow`** | Annotasks | Fast preview video at 8x speed |
| **`Shift + Down Arrow`** | Annotasks | Slow down video to 2x speed for segmenting |
| **`C`** | Annotasks | Create discrete action segment / backfill range |
| **`Shift + G`** | Annotasks | Trigger VLA caption generation |
| **`Ctrl + B`** | Annotasks | Open / close Label Bank |

---

## 📊 File Architecture

* [`main.py`](file:///c:/Users/princ/Downloads/Annotation/main.py): CLI and GUI entry point script.
* [`gui_app.py`](file:///c:/Users/princ/Downloads/Annotation/gui_app.py): Desktop GUI dashboard (Live Preview, OAG cards, History, Rules, Settings).
* [`clipboard_listener.py`](file:///c:/Users/princ/Downloads/Annotation/clipboard_listener.py): Background global hotkey listener (`pynput`), image buffer reader (`ImageGrab`), and auto-clipboard manager.
* [`vla_engine.py`](file:///c:/Users/princ/Downloads/Annotation/vla_engine.py): Multimodal vision engine using Gemini 2.5 Flash (`google-genai` SDK) with JSON schema output.
* [`vla_validator.py`](file:///c:/Users/princ/Downloads/Annotation/vla_validator.py): Rule validation engine checking negative word lists and sentence structure.
* [`config.py`](file:///c:/Users/princ/Downloads/Annotation/config.py): Configuration loader and settings persistence.
