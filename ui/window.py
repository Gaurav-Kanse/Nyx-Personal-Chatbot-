import customtkinter as ctk
from tkinter import scrolledtext, messagebox
import threading
from core.assistant import Assistant
from core.config import Config
from core.personality import list_personalities

class NyxUI:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.assistant = Assistant()
        self.root.title("Nyx - Local AI Assistant")
        self.root.geometry(f"{Config.UI_WIDTH}x{Config.UI_HEIGHT}")
        ctk.set_appearance_mode(Config.UI_THEME)
        ctk.set_default_color_theme("blue")

        self.setup_ui()
        self.update_status()

    def setup_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self.root, fg_color="#1e1e1e")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text="NYX - Local AI Assistant",
            font=("Arial", 20, "bold"),
            text_color="#00d4ff"
        )
        title.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Status: Initializing...",
            font=("Arial", 10),
            text_color="#808080"
        )
        self.status_label.grid(row=1, column=0, sticky="w", pady=(5, 0))

        chat_frame = ctk.CTkFrame(self.root)
        chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap="word",
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Courier", 10),
            state="disabled"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        input_frame = ctk.CTkFrame(self.root)
        input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message here...",
            font=("Arial", 12)
        )
        self.input_field.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_field.bind("<Return>", lambda e: self.send_message())

        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            command=self.send_message,
            width=80,
            font=("Arial", 12)
        )
        self.send_button.grid(row=0, column=1)

        control_frame = ctk.CTkFrame(self.root)
        control_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        control_frame.grid_columnconfigure(1, weight=1)

        self.voice_button = ctk.CTkButton(
            control_frame,
            text="🎤 Voice",
            command=self.toggle_voice,
            width=100,
            font=("Arial", 10)
        )
        self.voice_button.grid(row=0, column=0, padx=(0, 5))

        self.personality_menu = ctk.CTkComboBox(
            control_frame,
            values=list_personalities(),
            command=self.change_personality,
            font=("Arial", 10)
        )
        self.personality_menu.grid(row=0, column=1, padx=5, sticky="ew")
        self.personality_menu.set("default")

        self.clear_button = ctk.CTkButton(
            control_frame,
            text="Clear",
            command=self.clear_chat,
            width=80,
            font=("Arial", 10)
        )
        self.clear_button.grid(row=0, column=2, padx=(5, 0))

    def send_message(self):
        message = self.input_field.get().strip()
        if not message:
            return

        self.add_message("You", message)
        self.input_field.delete(0, "end")

        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()

    def process_message(self, message: str):
        response = self.assistant.process_text(message)

        self.root.after(0, self.add_message, "Nyx", response)

        if Config.ENABLE_VOICE:
            self.root.after(0, self.assistant.speak, response)

    def toggle_voice(self):
        threading.Thread(target=self.listen_for_voice, daemon=True).start()

    def listen_for_voice(self):
        self.root.after(0, self.send_button.configure, {"state": "disabled"})

        if self.assistant.listen_for_wakeword():
            self.add_message("Nyx", "Listening...")

        self.root.after(0, self.send_button.configure, {"state": "normal"})

    def change_personality(self, personality: str):
        self.assistant.set_personality(personality)
        self.add_message("Nyx", f"Personality changed to {personality}")

    def add_message(self, sender: str, message: str):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"{sender}: {message}\n\n")
        self.chat_display.see("end")
        self.chat_display.config(state="disabled")

    def clear_chat(self):
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.config(state="disabled")
        self.assistant.clear_history()

    def update_status(self):
        status = self.assistant.check_status()
        status_text = f"LLM: {'✓' if status['llm'] else '✗'} | STT: ✓ | TTS: ✓ | Voice: {'✓' if status['wakeword'] else '✗'}"
        self.status_label.configure(text=f"Status: {status_text}")

        self.root.after(5000, self.update_status)

    def run(self):
        self.root.mainloop()
