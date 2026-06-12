"""
ui/window.py
Nyx UI — CustomTkinter chat interface with memory command support.
"""

import customtkinter as ctk
from tkinter import scrolledtext
import threading
from core.assistant import Assistant
from core.config import Config
from core.personality import list_personalities
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NyxUI:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.assistant = Assistant()
        self.root.title("Nyx — Local AI Assistant")
        self.root.geometry(f"{Config.UI_WIDTH}x{Config.UI_HEIGHT}")
        ctk.set_appearance_mode(Config.UI_THEME)
        ctk.set_default_color_theme("blue")

        self.setup_ui()
        self._show_welcome()
        self.update_status()

    # ------------------------------------------------------------------ #
    # UI CONSTRUCTION                                                      #
    # ------------------------------------------------------------------ #

    def setup_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────────────────── #
        header_frame = ctk.CTkFrame(self.root, fg_color="#1a1a2e")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header_frame.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text="◈  NYX",
            font=("Arial", 22, "bold"),
            text_color="#00d4ff",
        )
        title.grid(row=0, column=0, sticky="w", padx=10, pady=6)

        self.user_label = ctk.CTkLabel(
            header_frame,
            text=f"Hello, {self.assistant.brain.get_user_name()} 👋",
            font=("Arial", 11),
            text_color="#a0a0c0",
        )
        self.user_label.grid(row=0, column=1, sticky="e", padx=10)

        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Status: Initializing…",
            font=("Arial", 9),
            text_color="#606080",
        )
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 6))

        # ── Chat display ──────────────────────────────────────────────── #
        chat_frame = ctk.CTkFrame(self.root)
        chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap="word",
            bg="#12121f",
            fg="#e0e0ff",
            font=("Courier", 10),
            insertbackground="#00d4ff",
            state="disabled",
            relief="flat",
            borderwidth=0,
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Configure coloured tags for roles
        self.chat_display.tag_configure("user_tag",   foreground="#00d4ff", font=("Courier", 10, "bold"))
        self.chat_display.tag_configure("nyx_tag",    foreground="#bd93f9", font=("Courier", 10, "bold"))
        self.chat_display.tag_configure("system_tag", foreground="#50fa7b", font=("Courier", 10, "italic"))
        self.chat_display.tag_configure("cmd_tag",    foreground="#ffb86c", font=("Courier", 10, "bold"))

        # ── Input row ─────────────────────────────────────────────────── #
        input_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=4)
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="Ask Nyx something… or type /help for commands",
            font=("Arial", 12),
            height=36,
        )
        self.input_field.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.input_field.bind("<Return>", lambda e: self.send_message())

        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            command=self.send_message,
            width=70,
            height=36,
            font=("Arial", 12, "bold"),
            fg_color="#3d5afe",
            hover_color="#5c7cfa",
        )
        self.send_button.grid(row=0, column=1)

        # ── Control bar ───────────────────────────────────────────────── #
        control_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        control_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        control_frame.grid_columnconfigure(1, weight=1)

        self.voice_button = ctk.CTkButton(
            control_frame,
            text="🎤 Voice",
            command=self.toggle_voice,
            width=90,
            height=30,
            font=("Arial", 10),
            fg_color="#2d3561",
            hover_color="#3d4a80",
        )
        self.voice_button.grid(row=0, column=0, padx=(0, 6))

        self.personality_menu = ctk.CTkComboBox(
            control_frame,
            values=list_personalities(),
            command=self.change_personality,
            font=("Arial", 10),
            height=30,
        )
        self.personality_menu.grid(row=0, column=1, padx=6, sticky="ew")
        self.personality_menu.set("default")

        self.clear_button = ctk.CTkButton(
            control_frame,
            text="Clear",
            command=self.clear_chat,
            width=70,
            height=30,
            font=("Arial", 10),
            fg_color="#3a1a1a",
            hover_color="#5a2a2a",
        )
        self.clear_button.grid(row=0, column=2, padx=(6, 0))

    # ------------------------------------------------------------------ #
    # WELCOME MESSAGE                                                      #
    # ------------------------------------------------------------------ #

    def _show_welcome(self):
        name = self.assistant.brain.get_user_name()
        self.add_message(
            "Nyx",
            f"Hey {name}! I'm Nyx, your local AI assistant. 🤖\n"
            "Type /help to see memory commands like /name, /notes, /memory.",
            tag="system_tag",
        )

    # ------------------------------------------------------------------ #
    # MESSAGING                                                            #
    # ------------------------------------------------------------------ #

    def send_message(self):
        message = self.input_field.get().strip()
        if not message:
            return

        is_cmd = message.startswith("/")
        self.add_message("You", message, tag="cmd_tag" if is_cmd else "user_tag")
        self.input_field.delete(0, "end")
        self.send_button.configure(state="disabled")

        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()

    def process_message(self, message: str):
        response = self.assistant.process_text(message)
        self.root.after(0, self.add_message, "Nyx", response)
        self.root.after(0, self.send_button.configure, {"state": "normal"})
        # Refresh user label in case /name was used
        self.root.after(0, self._refresh_user_label)

        if Config.ENABLE_VOICE and not message.startswith("/"):
            self.root.after(0, self.assistant.speak, response)

    def add_message(self, sender: str, message: str, tag: str = "nyx_tag"):
        self.chat_display.config(state="normal")

        # Sender badge
        sender_tag = "user_tag" if sender == "You" else tag
        self.chat_display.insert("end", f"{sender}: ", sender_tag)
        self.chat_display.insert("end", f"{message}\n\n")

        self.chat_display.see("end")
        self.chat_display.config(state="disabled")

    # ------------------------------------------------------------------ #
    # VOICE                                                                #
    # ------------------------------------------------------------------ #

    def toggle_voice(self):
        threading.Thread(target=self.listen_for_voice, daemon=True).start()

    def listen_for_voice(self):
        self.root.after(0, self.voice_button.configure, {"state": "disabled", "text": "🎙️ Listening…"})
        if hasattr(self.assistant, "listen_for_wakeword"):
            self.assistant.listen_for_wakeword()
        self.root.after(0, self.voice_button.configure, {"state": "normal", "text": "🎤 Voice"})

    # ------------------------------------------------------------------ #
    # CONTROLS                                                             #
    # ------------------------------------------------------------------ #

    def change_personality(self, personality: str):
        self.assistant.set_personality(personality)
        self.add_message("Nyx", f"Switched to **{personality}** personality. 🎭", tag="system_tag")

    def clear_chat(self):
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.config(state="disabled")
        self.assistant.clear_history()
        self.add_message("Nyx", "History cleared. Fresh start! ✨", tag="system_tag")

    # ------------------------------------------------------------------ #
    # STATUS                                                               #
    # ------------------------------------------------------------------ #

    def _refresh_user_label(self):
        name = self.assistant.brain.get_user_name()
        self.user_label.configure(text=f"Hello, {name} 👋")

    def update_status(self):
        status = self.assistant.check_status()
        llm_icon   = "✓" if status["llm"]      else "✗"
        wake_icon  = "✓" if status["wakeword"]  else "✗"
        model_str  = status.get("active_model", "—")
        mem_str    = status.get("memory",       "—")
        auto_str   = status.get("automation",   "—")

        status_text = (
            f"LLM: {llm_icon} [{model_str}]  "
            f"STT: ✓  TTS: ✓  Voice: {wake_icon}  "
            f"Mem: {mem_str}  "
            f"Auto: {auto_str}"
        )
        self.status_label.configure(text=f"Status: {status_text}")
        self.root.after(8000, self.update_status)

    # ------------------------------------------------------------------ #
    # MAIN LOOP                                                            #
    # ------------------------------------------------------------------ #

    def run(self):
        self.root.mainloop()
