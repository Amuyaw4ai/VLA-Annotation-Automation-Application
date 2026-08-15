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
        self.root.geometry("850x680")
        self.root.minsize(750, 580)

        # Style configuration
        self.setup_styles()

        # Connect listener callback to UI updater
        clipboard_service.callback = self.on_frame_processed

        # Build UI layout
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

        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), background=self.accent_color, foreground="#11111b")
        self.style.map("Action.TButton", background=[("active", "#b4befe")])

    def build_ui(self):
        # Header bar
        header_frame = ttk.Frame(self.root, padding=(15, 10))
        header_frame.pack(fill="x")

        title_label = ttk.Label(header_frame, text="⚡ VLA Annotation Automation", style="Header.TLabel")
        title_label.pack(side="left")

        hotkey_str = config.get("global_hotkey", "<alt>+<space>")
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

        instr_text = "Press Win + Shift + S to snip video frame ➔ Press Alt + Space anywhere ➔ Caption is auto-copied!"
        tk.Label(banner_frame, text=instr_text, font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.accent_color).pack(side="left")

        btn_manual = ttk.Button(banner_frame, text="Manual Process Clipboard", style="Action.TButton", command=self.trigger_manual_snip)
        btn_manual.pack(side="right")

        # Result Details Card
        self.result_card = tk.Frame(self.tab_live, bg=self.card_bg, padx=15, pady=15)
        self.result_card.pack(fill="both", expand=True)

        # High-Level Caption Output Section
        caption_header = tk.Frame(self.result_card, bg=self.card_bg)
        caption_header.pack(fill="x", pady=(0, 5))

        tk.Label(caption_header, text="High-Level Caption (T1) - Auto-Copied:", font=("Segoe UI", 11, "bold"), bg=self.card_bg, fg=self.success_color).pack(side="left")
        self.latency_var = tk.StringVar(value="")
        tk.Label(caption_header, textvariable=self.latency_var, font=("Segoe UI", 9), bg=self.card_bg, fg="#9399b2").pack(side="right")

        self.caption_text = tk.Text(self.result_card, height=3, font=("Segoe UI", 11), bg="#181825", fg=self.text_color, wrap="word", relief="flat", padx=10, pady=8)
        self.caption_text.pack(fill="x", pady=(0, 10))
        self.caption_text.insert("1.0", "No frame processed yet. Take a screenshot (Win+Shift+S) and press Alt+Space!")

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
        self.model_combo = ttk.Combobox(settings_card, values=["gemini-2.5-flash", "gemini-2.0-flash"], width=25, state="readonly")
        self.model_combo.grid(row=1, column=1, sticky="w", padx=10, pady=8)
        self.model_combo.set(config.get("gemini_model", "gemini-2.5-flash"))

        # Global Hotkey
        tk.Label(settings_card, text="Global Hotkey:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_color).grid(row=2, column=0, sticky="w", pady=8)
        self.hotkey_entry = ttk.Entry(settings_card, width=25)
        self.hotkey_entry.grid(row=2, column=1, sticky="w", padx=10, pady=8)
        self.hotkey_entry.insert(0, config.get("global_hotkey", "<alt>+<space>"))

        # Toggles
        self.auto_copy_var = tk.BooleanVar(value=config.get("auto_copy", True))
        ttk.Checkbutton(settings_card, text="Auto-copy caption to clipboard on snip", variable=self.auto_copy_var).grid(row=3, column=1, sticky="w", pady=8)

        self.audio_var = tk.BooleanVar(value=config.get("play_audio", True))
        ttk.Checkbutton(settings_card, text="Play audio chime feedback on success", variable=self.audio_var).grid(row=4, column=1, sticky="w", pady=8)

        # Save Button
        btn_save = ttk.Button(settings_card, text="Save Configuration", style="Action.TButton", command=self.save_settings)
        btn_save.grid(row=5, column=1, sticky="w", pady=20)

    def trigger_manual_snip(self):
        self.status_var.set("Processing clipboard image...")
        self.root.update_idletasks()
        clipboard_service._on_hotkey()

    def on_frame_processed(self, result: Dict[str, Any]):
        # Schedule update on main GUI thread
        self.root.after(0, lambda: self._update_ui_with_result(result))

    def _update_ui_with_result(self, result: Dict[str, Any]):
        if "error" in result:
            self.caption_text.delete("1.0", "end")
            self.caption_text.insert("1.0", f"Error: {result['error']}")
            self.rule_status_var.set(f"Error: {result['error']}")
            self.rule_status_label.config(fg=self.danger_color)
            self.status_var.set("Ready for Snip (Error encountered)")
            return

        # Update Caption
        caption = result.get("high_level_caption", "")
        self.caption_text.delete("1.0", "end")
        self.caption_text.insert("1.0", caption)

        # Update OAG
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
