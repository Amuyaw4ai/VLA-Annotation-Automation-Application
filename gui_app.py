import sys
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
from typing import Dict, Any

from config import config
from clipboard_listener import clipboard_service
from vla_engine import engine

class VLAAppGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("VLA Annotation Automation Assistant - Annotasks")
        self.current_ui_mode = config.get("ui_mode", "full")
        self.is_pinned = config.get("pinned_top", True)
        self.is_locked = config.get("position_locked", False)

        if self.current_ui_mode == "mini":
            self.root.minsize(350, 90)
            self.root.maxsize(800, 200)
            self.root.geometry("440x115")
        else:
            self.root.minsize(750, 580)
            self.root.geometry("850x680")

        # Style configuration
        self.setup_styles()

        # Connect listener callback to UI updater
        clipboard_service.callback = self.on_frame_processed

        # Build UI layout according to saved mode
        if self.current_ui_mode == "mini":
            self.build_mini_ui()
        else:
            self.build_ui()

        # Start global hotkey listener
        clipboard_service.start()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Dark theme palette
        self.bg_color = "#1e1e2e"
        self.card_bg = "#2b2b3b"
        self.accent_color = "#89b4fa"
        self.success_color = "#a6e3a1"
        self.danger_color = "#f38ba8"
        self.text_color = "#cdd6f4"

        self.root.configure(bg=self.bg_color)

        self.style.configure(".", background=self.bg_color, foreground=self.text_color)
        self.style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.card_bg, foreground=self.text_color, padding=[12, 6])
        self.style.map("TNotebook.Tab", background=[("selected", self.accent_color)], foreground=[("selected", "#11111b")])

        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("Card.TFrame", background=self.card_bg, relief="flat", borderwidth=1)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground=self.accent_color)
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 11, "bold"), foreground=self.text_color)
        self.style.configure("Status.TLabel", font=("Segoe UI", 9, "italic"), foreground="#9399b2")

        self.style.map("Action.TButton", background=[("active", "#b4befe")])

        # Window state flags
        self.is_pinned = config.get("pinned_top", True)
        self.is_locked = config.get("position_locked", False)
        self.current_ui_mode = config.get("ui_mode", "full")

        # Set always on top if pinned
        if self.is_pinned:
            self.root.attributes("-topmost", True)

    def _on_mini_scroll(self, event):
        """Invisible Mouse-Wheel Scrolling for compact text box."""
        if hasattr(self, "mini_caption_text") and self.mini_caption_text.winfo_exists():
            if event.delta:
                self.mini_caption_text.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def toggle_pin_top(self):
        self.is_pinned = not self.is_pinned
        config.set("pinned_top", self.is_pinned)
        self.root.attributes("-topmost", self.is_pinned)
        if hasattr(self, "pin_btn"):
            self.pin_btn.config(text="📌 Pinned" if self.is_pinned else "📌 Unpinned")

    def toggle_lock_pos(self):
        self.is_locked = not self.is_locked
        config.set("position_locked", self.is_locked)
        if hasattr(self, "lock_btn"):
            self.lock_btn.config(text="🔒 Locked" if self.is_locked else "🔓 Unlocked")

    def toggle_ui_mode(self):
        new_mode = "mini" if self.current_ui_mode == "full" else "full"
        self.current_ui_mode = new_mode
        config.set("ui_mode", new_mode)

        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        if new_mode == "mini":
            self.root.minsize(350, 90)
            self.root.maxsize(800, 180)
            self.root.geometry("440x115")
            self.root.resizable(True, True)
            self.build_mini_ui()
        else:
            self.root.maxsize(3000, 3000)
            self.root.minsize(750, 580)
            self.root.geometry("850x680")
            self.root.resizable(True, True)
            self.build_ui()

    def build_mini_ui(self):
        # Master Mini Frame (Sleek compact bar)
        mini_master = tk.Frame(self.root, bg=self.card_bg, padx=4, pady=4)
        mini_master.pack(fill="both", expand=True)

        # Column 1 (Left ~40%): Caption Text & Badges (Invisible Mouse-Wheel Scroll)
        col1 = tk.Frame(mini_master, bg="#181825", padx=6, pady=4)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 2))

        header_sub = tk.Frame(col1, bg="#181825")
        header_sub.pack(fill="x", pady=(0, 2))

        cur_mode = self.mode_var.get() if hasattr(self, "mode_var") else config.get("annotation_mode", "high_level")
        mode_text = "T2 Detailed" if cur_mode == "detailed" else "T1 High-Level"
        self.mini_mode_label = tk.Label(header_sub, text=mode_text, font=("Segoe UI", 8, "bold"), bg="#181825", fg=self.success_color)
        self.mini_mode_label.pack(side="left")

        self.mini_latency_label = tk.Label(header_sub, text="", font=("Segoe UI", 8), bg="#181825", fg="#9399b2")
        self.mini_latency_label.pack(side="right")

        # Invisible-scroll text box
        self.mini_caption_text = tk.Text(col1, height=3, font=("Segoe UI", 9), bg="#181825", fg=self.text_color, wrap="word", relief="flat", borderwidth=0)
        self.mini_caption_text.pack(fill="both", expand=True)

        # Pre-fill active caption if available
        if clipboard_service.active_captions and cur_mode in clipboard_service.active_captions:
            cap_data = clipboard_service.active_captions[cur_mode]
            self.mini_caption_text.insert("1.0", cap_data.get("high_level_caption", ""))
        else:
            self.mini_caption_text.insert("1.0", "Win+Shift+S snip ➔ Ctrl+Space")

        self.mini_caption_text.bind("<MouseWheel>", self._on_mini_scroll)

        # Column 2 (Center ~30%): Toggle Icons & Controls
        col2 = tk.Frame(mini_master, bg=self.card_bg, padx=2)
        col2.pack(side="left", fill="y", padx=2)

        m_btn_lbl = f"Mode: {cur_mode.upper()}"
        self.mini_mode_btn = tk.Button(col2, text=m_btn_lbl, font=("Segoe UI", 7, "bold"), bg="#313244", fg=self.accent_color, relief="flat", pady=1, command=self._toggle_mini_mode_val)
        self.mini_mode_btn.pack(fill="x", pady=1)

        auto_st = "⚡ Auto" if config.get("auto_detect_clipboard", False) else "🎯 Manual"
        self.mini_auto_btn = tk.Button(col2, text=auto_st, font=("Segoe UI", 7), bg="#313244", fg=self.text_color, relief="flat", pady=1, command=self._toggle_mini_auto_val)
        self.mini_auto_btn.pack(fill="x", pady=1)

        self.pin_btn = tk.Button(col2, text="📌 Pin" if self.is_pinned else "📌 Unpin", font=("Segoe UI", 7), bg="#313244", fg=self.text_color, relief="flat", pady=1, command=self.toggle_pin_top)
        self.pin_btn.pack(fill="x", pady=1)

        self.lock_btn = tk.Button(col2, text="🔒 Lock" if self.is_locked else "🔓 Lock", font=("Segoe UI", 7), bg="#313244", fg=self.text_color, relief="flat", pady=1, command=self.toggle_lock_pos)
        self.lock_btn.pack(fill="x", pady=1)

        btn_expand = tk.Button(col2, text="↗ Full", font=("Segoe UI", 7, "bold"), bg=self.accent_color, fg="#11111b", relief="flat", pady=1, command=self.toggle_ui_mode)
        btn_expand.pack(fill="x", pady=(1, 0))

        # Column 3 (Right ~30%): Manual Drop & Process Action Zone
        col3 = tk.Frame(mini_master, bg="#181825", padx=4, pady=4)
        col3.pack(side="left", fill="both", padx=(2, 0))

        tk.Label(col3, text="📥 Drop / Action", font=("Segoe UI", 8, "bold"), bg="#181825", fg=self.text_color).pack(pady=(0, 2))

        btn_proc = tk.Button(col3, text="⚡ Process\nClipboard", font=("Segoe UI", 8, "bold"), bg=self.accent_color, fg="#11111b", relief="flat", command=self.trigger_manual_snip)
        btn_proc.pack(fill="both", expand=True)

    def _toggle_mini_mode_val(self):
        cur = self.mode_var.get()
        new_val = "detailed" if cur == "high_level" else "high_level"
        self.mode_var.set(new_val)
        self.on_mode_changed()
        if hasattr(self, "mini_mode_btn"):
            self.mini_mode_btn.config(text=f"Mode: {new_val.upper()}")

    def _toggle_mini_auto_val(self):
        cur = config.get("auto_detect_clipboard", False)
        new_val = not cur
        config.set("auto_detect_clipboard", new_val)
        if hasattr(self, "auto_detect_var"):
            self.auto_detect_var.set(new_val)
        if hasattr(self, "mini_auto_btn"):
            self.mini_auto_btn.config(text="⚡ Auto" if new_val else "🎯 Manual")

    def build_ui(self):
        # Header bar
        header_frame = ttk.Frame(self.root, padding=(15, 10))
        header_frame.pack(fill="x")

        title_label = ttk.Label(header_frame, text="⚡ VLA Annotation Automation", style="Header.TLabel")
        title_label.pack(side="left")

        # Mini mode switch button in header
        btn_mini = tk.Button(header_frame, text="↙ Mini Mode", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.accent_color, relief="flat", command=self.toggle_ui_mode)
        btn_mini.pack(side="left", padx=15)

        hotkey_str = config.get("global_hotkey", "<ctrl>+<space>")
        self.status_var = tk.StringVar(value=f"Hotkey: [{hotkey_str}] Active | Ready for Snip")
        status_badge = ttk.Label(header_frame, textvariable=self.status_var, style="Status.TLabel")
        status_badge.pack(side="right")

        # Notebook tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Tab 1: Live Snip & Caption
        self.tab_live = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_live, text="  Live Snip & Caption  ")
        self.build_live_tab()

        # Tab 2: History Log
        self.tab_history = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_history, text="  History Log  ")
        self.build_history_tab()

        # Tab 3: Guidelines & Rules
        self.tab_rules = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_rules, text="  Rules & Shortcuts  ")
        self.build_rules_tab()

        # Tab 4: Settings
        self.tab_settings = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_settings, text="  Settings  ")
        self.build_settings_tab()

    def build_live_tab(self):
        # Instructions / Trigger Card
        banner_frame = tk.Frame(self.tab_live, bg=self.card_bg, padx=15, pady=12)
        banner_frame.pack(fill="x", pady=(0, 12))

        instr_text = "Press Win+Shift+S to snip ➔ Press Ctrl+Space (or enable Auto-Snip in Settings)!"
        tk.Label(banner_frame, text=instr_text, font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.accent_color).pack(side="left")

        btn_manual = ttk.Button(banner_frame, text="Manual Process Clipboard", style="Action.TButton", command=self.trigger_manual_snip)
        btn_manual.pack(side="right")

        # Mode Switcher Bar
        mode_frame = tk.Frame(self.tab_live, bg=self.card_bg, padx=15, pady=8)
        mode_frame.pack(fill="x", pady=(0, 10))

        tk.Label(mode_frame, text="Annotation Mode:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_color).pack(side="left", padx=(0, 10))

        self.mode_var = tk.StringVar(value=config.get("annotation_mode", "high_level"))
        rb_t1 = tk.Radiobutton(mode_frame, text="High-Level Overview (T1)", variable=self.mode_var, value="high_level", bg=self.card_bg, fg=self.text_color, selectcolor="#181825", font=("Segoe UI", 10), command=self.on_mode_changed)
        rb_t1.pack(side="left", padx=5)

        rb_t2 = tk.Radiobutton(mode_frame, text="Detailed Segment Action (T2)", variable=self.mode_var, value="detailed", bg=self.card_bg, fg=self.text_color, selectcolor="#181825", font=("Segoe UI", 10), command=self.on_mode_changed)
        rb_t2.pack(side="left", padx=5)

        # Result Details Card
        self.result_card = tk.Frame(self.tab_live, bg=self.card_bg, padx=15, pady=15)
        self.result_card.pack(fill="both", expand=True)

        # Caption Output Section Header
        caption_header = tk.Frame(self.result_card, bg=self.card_bg)
        caption_header.pack(fill="x", pady=(0, 5))

        self.caption_title_var = tk.StringVar(value="Caption Output - Auto-Copied:")
        self._update_caption_title()

        tk.Label(caption_header, textvariable=self.caption_title_var, font=("Segoe UI", 11, "bold"), bg=self.card_bg, fg=self.success_color).pack(side="left")
        self.latency_var = tk.StringVar(value="")
        tk.Label(caption_header, textvariable=self.latency_var, font=("Segoe UI", 9), bg=self.card_bg, fg="#9399b2").pack(side="right")

        self.caption_text = tk.Text(self.result_card, height=3, font=("Segoe UI", 11), bg="#181825", fg=self.text_color, wrap="word", relief="flat", padx=10, pady=8)
        self.caption_text.pack(fill="x", pady=(0, 10))
        self.caption_text.insert("1.0", "No frame processed yet. Take a screenshot (Win+Shift+S) and press Ctrl+Space!")

        btn_copy_cap = tk.Button(self.result_card, text="📋 Copy Caption", font=("Segoe UI", 9, "bold"), bg=self.accent_color, fg="#11111b", relief="flat", command=self.copy_caption)
        btn_copy_cap.pack(anchor="e", pady=(0, 12))

        # OAG Breakdown Grid
        oag_frame = tk.Frame(self.result_card, bg=self.card_bg)
        oag_frame.pack(fill="x", pady=(0, 12))

        # Object
        tk.Label(oag_frame, text="Object:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_color).grid(row=0, column=0, sticky="w", pady=4)
        self.obj_var = tk.StringVar(value="-")
        tk.Label(oag_frame, textvariable=self.obj_var, font=("Segoe UI", 10), bg=self.card_bg, fg=self.accent_color).grid(row=0, column=1, sticky="w", padx=10, pady=4)

        # Action
        tk.Label(oag_frame, text="Action:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_color).grid(row=1, column=0, sticky="w", pady=4)
        self.act_var = tk.StringVar(value="-")
        tk.Label(oag_frame, textvariable=self.act_var, font=("Segoe UI", 10), bg=self.card_bg, fg=self.accent_color).grid(row=1, column=1, sticky="w", padx=10, pady=4)

        # Goal
        tk.Label(oag_frame, text="Goal:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_color).grid(row=2, column=0, sticky="w", pady=4)
        self.goal_var = tk.StringVar(value="-")
        tk.Label(oag_frame, textvariable=self.goal_var, font=("Segoe UI", 10), bg=self.card_bg, fg=self.accent_color).grid(row=2, column=1, sticky="w", padx=10, pady=4)

        # Suggested Segments
        tk.Label(self.result_card, text="Suggested Discrete Segments (T2):", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_color).pack(anchor="w", pady=(5, 2))
        self.segments_list = tk.Listbox(self.result_card, height=4, font=("Segoe UI", 9), bg="#181825", fg=self.text_color, selectbackground=self.accent_color, relief="flat", borderwidth=0)
        self.segments_list.pack(fill="x", pady=(0, 10))

        # Rule Compliance Status
        self.rule_status_var = tk.StringVar(value="Rule Status: Ready")
        self.rule_status_label = tk.Label(self.result_card, textvariable=self.rule_status_var, font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.success_color)
        self.rule_status_label.pack(anchor="w")

    def build_history_tab(self):
        btn_frame = tk.Frame(self.tab_history, bg=self.bg_color)
        btn_frame.pack(fill="x", pady=(0, 10))

        tk.Label(btn_frame, text="Session Annotation History", font=("Segoe UI", 11, "bold"), bg=self.bg_color, fg=self.accent_color).pack(side="left")
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_history).pack(side="right", padx=5)

        self.history_tree = ttk.Treeview(self.tab_history, columns=("time", "caption", "valid", "latency"), show="headings", height=15)
        self.history_tree.heading("time", text="Time")
        self.history_tree.heading("caption", text="High-Level Caption (T1)")
        self.history_tree.heading("valid", text="Rules")
        self.history_tree.heading("latency", text="Latency")

        self.history_tree.column("time", width=80, anchor="center")
        self.history_tree.column("caption", width=500, anchor="w")
        self.history_tree.column("valid", width=80, anchor="center")
        self.history_tree.column("latency", width=80, anchor="center")

        self.history_tree.pack(fill="both", expand=True)
        self.history_tree.bind("<Double-1>", self.on_history_double_click)

        self.refresh_history()

    def build_rules_tab(self):
        rules_card = tk.Frame(self.tab_rules, bg=self.card_bg, padx=15, pady=15)
        rules_card.pack(fill="both", expand=True)

        tk.Label(rules_card, text="Strict VLA Quality Guidelines Checklist", font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.accent_color).pack(anchor="w", pady=(0, 10))

        guidelines_text = """
✅ DO:
• Simple English & active/passive factual descriptions only.
• Use the exact formula: "[Object] is [Action] [Goal]."
• Focus on visible physical objects and immediate actions.
• Keep video completion time under 4 minutes total (~1.5s per snip).

❌ STRICTLY DO NOT MENTION:
• 'operator', 'worker', 'person', 'people'
• 'left hand', 'right hand', 'hand', 'hands', 'arms', 'robotic arm'
• Speculated intentions, unseen thoughts, or unverified goals.

⌨️ Platform Hotkey Quick Reference (Annotasks):
• Shift + Up Arrow: Preview video at 8x speed.
• Shift + Down Arrow: Slow down video to 2x speed for segmenting.
• C: Generate segment range / backfill segment.
• G: Trigger automatic VLA Caption generation.
• Ctrl + B: Open / close Label Bank.
"""
        txt = tk.Text(rules_card, font=("Consolas", 10), bg="#181825", fg=self.text_color, wrap="word", relief="flat", padx=10, pady=10)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", guidelines_text)
        txt.config(state="disabled")

    def build_settings_tab(self):
        settings_card = tk.Frame(self.tab_settings, bg=self.card_bg, padx=20, pady=20)
        settings_card.pack(fill="both", expand=True)

        # API Key
        tk.Label(settings_card, text="Gemini API Key:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_color).grid(row=0, column=0, sticky="w", pady=8)
        self.api_key_entry = ttk.Entry(settings_card, width=45, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky="w", padx=10, pady=8)
        self.api_key_entry.insert(0, config.get("gemini_api_key", ""))

        # Model Selector
        tk.Label(settings_card, text="Vision Model:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_color).grid(row=1, column=0, sticky="w", pady=8)
        self.model_combo = ttk.Combobox(settings_card, values=["gemini-flash-latest", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-pro-latest"], width=25, state="readonly")
        self.model_combo.grid(row=1, column=1, sticky="w", padx=10, pady=8)
        self.model_combo.set(config.get("gemini_model", "gemini-flash-latest"))

        # Global Hotkey
        tk.Label(settings_card, text="Global Hotkey:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_color).grid(row=2, column=0, sticky="w", pady=8)
        self.hotkey_entry = ttk.Entry(settings_card, width=25)
        self.hotkey_entry.grid(row=2, column=1, sticky="w", padx=10, pady=8)
        self.hotkey_entry.insert(0, config.get("global_hotkey", "<ctrl>+<space>"))

        # Toggles
        self.auto_detect_var = tk.BooleanVar(value=config.get("auto_detect_clipboard", False))
        ttk.Checkbutton(settings_card, text="Autonomous Mode: Auto-generate caption on Win+Shift+S (no Ctrl+Space needed)", variable=self.auto_detect_var).grid(row=3, column=1, sticky="w", pady=4)

        self.auto_copy_var = tk.BooleanVar(value=config.get("auto_copy", True))
        ttk.Checkbutton(settings_card, text="Auto-copy generated caption to system clipboard", variable=self.auto_copy_var).grid(row=4, column=1, sticky="w", pady=4)

        self.audio_var = tk.BooleanVar(value=config.get("play_audio", True))
        ttk.Checkbutton(settings_card, text="Play audio chime feedback on success", variable=self.audio_var).grid(row=5, column=1, sticky="w", pady=4)

        # Save Button
        btn_save = ttk.Button(settings_card, text="Save Configuration", style="Action.TButton", command=self.save_settings)
        btn_save.grid(row=6, column=1, sticky="w", pady=16)

    def _update_caption_title(self):
        m = self.mode_var.get() if hasattr(self, "mode_var") else config.get("annotation_mode", "high_level")
        if m == "detailed":
            self.caption_title_var.set("Detailed Segment Action Caption (T2) - Auto-Copied:")
        else:
            self.caption_title_var.set("High-Level Overview Caption (T1) - Auto-Copied:")

    def on_mode_changed(self):
        new_mode = self.mode_var.get()
        config.set("annotation_mode", new_mode)
        self._update_caption_title()

        # Task 2: Reprocess or retrieve cached caption for active image in memory
        if clipboard_service.active_image is not None:
            import threading
            threading.Thread(target=clipboard_service.reprocess_active_image, args=(new_mode,), daemon=True).start()

    def trigger_manual_snip(self):
        self.status_var.set(f"Processing clipboard image ({self.mode_var.get().upper()} mode)...")
        self.root.update_idletasks()
        clipboard_service._on_hotkey()

    def on_frame_processed(self, result: Dict[str, Any]):
        # Schedule update on main GUI thread
        self.root.after(0, lambda: self._update_ui_with_result(result))

    def _update_ui_with_result(self, result: Dict[str, Any]):
        caption = result.get("high_level_caption", result.get("error", ""))
        lat = result.get("latency_seconds", 0)

        # Update Mini View widgets if present
        if hasattr(self, "mini_caption_text") and self.mini_caption_text.winfo_exists():
            self.mini_caption_text.delete("1.0", "end")
            self.mini_caption_text.insert("1.0", caption)
            mode_tag = "T2 Detailed" if result.get("annotation_mode") == "detailed" else "T1 High-Level"
            if hasattr(self, "mini_mode_label"):
                self.mini_mode_label.config(text=mode_tag)
            if hasattr(self, "mini_latency_label"):
                self.mini_latency_label.config(text=f"⏱️ {lat}s | 📋 Copied")

        # Update Full View widgets if present
        if hasattr(self, "caption_text") and self.caption_text.winfo_exists():
            if "error" in result:
                self.caption_text.delete("1.0", "end")
                self.caption_text.insert("1.0", f"Error: {result['error']}")
                self.rule_status_var.set(f"Error: {result['error']}")
                self.rule_status_label.config(fg=self.danger_color)
                self.status_var.set("Ready for Snip (Error encountered)")
                return

            self.caption_text.delete("1.0", "end")
            self.caption_text.insert("1.0", caption)

            if hasattr(self, "obj_var"):
                self.obj_var.set(result.get("object", "-"))
                self.act_var.set(result.get("action", "-"))
                self.goal_var.set(result.get("goal", "-"))

        # Update Latency
        lat = result.get("latency_seconds", 0)
        self.latency_var.set(f"Latency: {lat}s | Auto-Copied 📋")

        # Update Segments list
        self.segments_list.delete(0, "end")
        for seg in result.get("suggested_segments", []):
            self.segments_list.insert("end", f"• {seg}")

        # Update Rule Status
        if result.get("is_valid", False):
            self.rule_status_var.set("Rule Check: PASS ✅ (100% Client Compliant)")
            self.rule_status_label.config(fg=self.success_color)
        else:
            violations = ", ".join(result.get("violations", []))
            self.rule_status_var.set(f"Rule Warning ⚠️: {violations}")
            self.rule_status_label.config(fg=self.danger_color)

        hotkey_str = config.get("global_hotkey", "<alt>+<space>")
        self.status_var.set(f"Hotkey: [{hotkey_str}] Active | Ready for Next Snip")

        # Refresh history tab
        self.refresh_history()

    def copy_caption(self):
        cap = self.caption_text.get("1.0", "end-1c").strip()
        if cap and not cap.startswith("No frame"):
            pyperclip.copy(cap)
            messagebox.showinfo("Copied", "High-Level Caption copied to clipboard!")

    def refresh_history(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)

        for item in clipboard_service.history:
            t = item.get("timestamp", "-")
            cap = item.get("high_level_caption", item.get("error", "-"))
            valid = "✅ PASS" if item.get("is_valid") else "⚠️ ALERT"
            lat = f"{item.get('latency_seconds', '-')}s"
            self.history_tree.insert("", "end", values=(t, cap, valid, lat))

    def on_history_double_click(self, event):
        item_id = self.history_tree.focus()
        if item_id:
            vals = self.history_tree.item(item_id, "values")
            if len(vals) >= 2:
                pyperclip.copy(vals[1])
                messagebox.showinfo("Copied", f"Copied caption from history:\n\n'{vals[1]}'")

    def save_settings(self):
        config.set("gemini_api_key", self.api_key_entry.get().strip())
        config.set("gemini_model", self.model_combo.get())
        config.set("global_hotkey", self.hotkey_entry.get().strip())
        config.set("auto_detect_clipboard", self.auto_detect_var.get())
        config.set("auto_copy", self.auto_copy_var.get())
        config.set("play_audio", self.audio_var.get())

        # Re-init engine & restart listener with new hotkey
        engine._init_client()
        clipboard_service.stop()
        clipboard_service.start()

        messagebox.showinfo("Settings Saved", "Configuration updated successfully!")

    def on_close(self):
        clipboard_service.stop()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = VLAAppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
