"""
ui/window.py

Nyx — Minimal dark launcher UI
Three screens: Home · Voice · Chat
"""

import tkinter as tk
import customtkinter as ctk
import math
import threading

# ── Palette ──────────────────────────────────────────────────────────── #
C = {
    "bg":        "#050505",
    "card":      "#0e0e0e",
    "card_h":    "#141414",
    "border":    "#1a1a1a",
    "lime":      "#c8ff00",
    "lime_dim":  "#96bf00",
    "lime_dark": "#1c2800",
    "white":     "#f0f0f0",
    "dim":       "#666666",
    "faint":     "#333333",
    "bubble_u":  "#181818",
    "bubble_n":  "#101a08",
}

FONT      = "Segoe UI"
FONT_MONO = "Consolas"


# ═══════════════════════════════════════════════════════════════════════ #
# BLOB ORB                                                                #
# ═══════════════════════════════════════════════════════════════════════ #

class BlobOrb:
    """Four breathing ellipses on a canvas."""

    BLOBS = [
        {"rx": 16, "ry": 24, "ph": 0.0, "sp": 0.018},
        {"rx": 18, "ry": 20, "ph": 1.2, "sp": 0.022},
        {"rx": 15, "ry": 26, "ph": 2.4, "sp": 0.015},
        {"rx": 17, "ry": 22, "ph": 3.8, "sp": 0.020},
    ]

    def __init__(self, canvas, w=140, h=90):
        self.c, self.W, self.H, self.t = canvas, w, h, 0
        self._on = False
        self._gap = w // 4
        self._x0 = self._gap // 2

    def start(self):
        self._on = True
        self._tick()

    def stop(self):
        self._on = False

    def _tick(self):
        if not self._on:
            return
        self.c.delete("b")
        cy = self.H // 2
        for i, b in enumerate(self.BLOBS):
            cx = self._x0 + i * self._gap
            bx = 1 + .10 * math.sin(self.t * b["sp"] * 1.3 + b["ph"])
            by = 1 + .13 * math.cos(self.t * b["sp"] + b["ph"] + .5)
            rx, ry = b["rx"] * bx, b["ry"] * by
            self.c.create_oval(cx - rx, cy - ry, cx + rx, cy + ry,
                               fill=C["white"], outline="", tags="b")
        self.t += 1
        self.c.after(16, self._tick)


# ═══════════════════════════════════════════════════════════════════════ #
# RIPPLE                                                                  #
# ═══════════════════════════════════════════════════════════════════════ #

class Ripple:
    def __init__(self, canvas, cx, cy, color):
        self.c, self.cx, self.cy, self.color = canvas, cx, cy, color
        self._t, self._on = 0, False

    def start(self):
        self._on = True
        self._tick()

    def stop(self):
        self._on = False

    def _tick(self):
        if not self._on:
            return
        self.c.delete("r")
        for off in (0, .5):
            p = (self._t * .02 + off) % 1.0
            r = 26 + p * 18
            self.c.create_oval(self.cx - r, self.cy - r,
                               self.cx + r, self.cy + r,
                               outline=self.color, width=1, tags="r")
        self._t += 1
        self.c.after(16, self._tick)


# ═══════════════════════════════════════════════════════════════════════ #
# HOME SCREEN                                                             #
# ═══════════════════════════════════════════════════════════════════════ #

class HomeScreen(ctk.CTkFrame):
    """Dashboard / landing screen."""

    HISTORY = [
        ("Yojna Saathi build status",        "Voice"),
        ("Futuristic UI design tools 2026",   "Chat"),
        ("Samsung Solve for Tomorrow prep",   "Chat"),
    ]

    def __init__(self, master, *, user_name, on_voice, on_chat, **kw):
        super().__init__(master, fg_color=C["bg"], **kw)
        self._uname = user_name
        self._on_voice = on_voice
        self._on_chat = on_chat
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)       # history stretches

        # ── Greeting row ─────────────────────────────────────────────── #
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(22, 0))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top, text=f"Hi, {self._uname}",
            font=(FONT, 13), text_color=C["dim"],
        ).grid(row=0, column=0, sticky="w")

        initials = (self._uname[:2].upper()
                    if isinstance(self._uname, str) else "NY")
        ctk.CTkLabel(
            top, text=initials,
            font=(FONT, 9, "bold"), text_color=C["white"],
            fg_color=C["card_h"], corner_radius=15,
            width=30, height=30,
        ).grid(row=0, column=1, sticky="e")

        # ── Title ────────────────────────────────────────────────────── #
        ctk.CTkLabel(
            self, text="How can I\nhelp you?",
            font=(FONT, 26, "bold"), text_color=C["white"],
            justify="left", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(16, 20))

        # ── Action cards ─────────────────────────────────────────────── #
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        self._action_card(cards, 0,
                          icon="🎤", title="Voice",
                          fg=C["lime"], text_c="#000000",
                          cmd=self._on_voice)
        self._action_card(cards, 1,
                          icon="💬", title="Chat",
                          fg=C["card"], text_c=C["white"],
                          cmd=self._on_chat, border=C["border"])

        # ── History list ─────────────────────────────────────────────── #
        ctk.CTkLabel(
            self, text="Recent",
            font=(FONT, 11, "bold"), text_color=C["dim"],
        ).grid(row=3, column=0, sticky="nw", padx=20, pady=(0, 6))

        hist = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C["faint"],
            scrollbar_button_hover_color=C["dim"],
        )
        hist.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 14))
        hist.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        for i, (text, tag) in enumerate(self.HISTORY):
            self._hist_row(hist, i, text, tag)

    # ── helpers ──────────────────────────────────────────────────────── #

    def _action_card(self, parent, col, *, icon, title, fg, text_c,
                     cmd=None, border=None):
        kw = {"fg_color": fg, "corner_radius": 16, "height": 90}
        if border:
            kw.update(border_color=border, border_width=1)
        card = ctk.CTkFrame(parent, **kw)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, 4) if col == 0 else (4, 0))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(card, text=icon, font=(FONT, 22),
                     text_color=text_c,
                     ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 0))
        ctk.CTkLabel(card, text=title, font=(FONT, 13, "bold"),
                     text_color=text_c, anchor="sw",
                     ).grid(row=1, column=0, sticky="sw", padx=14, pady=(0, 12))

        if cmd:
            card.configure(cursor="hand2")
            card.bind("<Button-1>", lambda e: cmd())
            for ch in card.winfo_children():
                ch.bind("<Button-1>", lambda e: cmd())

    def _hist_row(self, parent, idx, text, tag):
        row = ctk.CTkFrame(parent, fg_color=C["card"],
                           corner_radius=10, height=40)
        row.grid(row=idx, column=0, sticky="ew", pady=(0, 4))
        row.grid_columnconfigure(0, weight=1)
        row.grid_propagate(False)

        ctk.CTkLabel(row, text=text, font=(FONT, 10),
                     text_color=C["dim"], anchor="w",
                     ).grid(row=0, column=0, sticky="w", padx=12, pady=10)

        ctk.CTkLabel(row, text=tag, font=(FONT, 8),
                     text_color=C["faint"],
                     ).grid(row=0, column=1, sticky="e", padx=12, pady=10)


# ═══════════════════════════════════════════════════════════════════════ #
# VOICE SCREEN                                                            #
# ═══════════════════════════════════════════════════════════════════════ #

class VoiceScreen(ctk.CTkFrame):
    def __init__(self, master, *, on_back, **kw):
        super().__init__(master, fg_color=C["bg"], **kw)
        self._on_back = on_back
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ── Top bar ──────────────────────────────────────────────────── #
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            top, text="←", width=32, height=32, corner_radius=16,
            fg_color=C["card"], hover_color=C["card_h"],
            font=(FONT, 16), text_color=C["dim"],
            command=self._on_back,
        ).grid(row=0, column=0, sticky="w")

        # Status pill
        pill = ctk.CTkFrame(top, fg_color=C["lime_dark"], corner_radius=10,
                            height=22)
        pill.grid(row=0, column=2, sticky="e")
        pill.grid_propagate(False)
        ctk.CTkLabel(pill, text="● listening",
                     font=(FONT, 8), text_color=C["lime"],
                     ).pack(padx=10, pady=2)

        # ── Badge ────────────────────────────────────────────────────── #
        ctk.CTkLabel(
            self, text="  NYX  ",
            font=(FONT_MONO, 9, "bold"), text_color="#000",
            fg_color=C["lime"], corner_radius=12, height=24,
        ).grid(row=1, column=0, pady=(20, 4))

        # ── Orb ──────────────────────────────────────────────────────── #
        orb_cv = tk.Canvas(self, width=140, height=90,
                           bg=C["bg"], highlightthickness=0)
        orb_cv.grid(row=2, column=0, pady=(0, 0))
        self._blob = BlobOrb(orb_cv)
        self._blob.start()

        # ── Subtitle ─────────────────────────────────────────────────── #
        ctk.CTkLabel(
            self, text="Speak now…",
            font=(FONT, 12), text_color=C["dim"],
        ).grid(row=3, column=0, pady=(0, 0))

        # ── Mic button ───────────────────────────────────────────────── #
        ctk.CTkButton(
            self, text="●", width=52, height=52, corner_radius=26,
            fg_color=C["lime"], hover_color=C["lime_dim"],
            font=(FONT, 20), text_color="#000",
        ).grid(row=4, column=0, pady=(8, 30))

    def destroy(self):
        self._blob.stop()
        super().destroy()


# ═══════════════════════════════════════════════════════════════════════ #
# CHAT SCREEN                                                             #
# ═══════════════════════════════════════════════════════════════════════ #

class ChatScreen(ctk.CTkFrame):
    """Minimal chat view, wired to core.assistant.Assistant."""

    def __init__(self, master, *, on_back, assistant=None,
                 user_name="User", **kw):
        super().__init__(master, fg_color=C["bg"], **kw)
        self._on_back = on_back
        self._assistant = assistant
        self._uname = user_name
        self._row = 0
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top bar ──────────────────────────────────────────────────── #
        top = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=46)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(1, weight=1)
        top.grid_propagate(False)

        ctk.CTkButton(
            top, text="←", width=32, height=32, corner_radius=16,
            fg_color="transparent", hover_color=C["card_h"],
            font=(FONT, 16), text_color=C["dim"],
            command=self._on_back,
        ).grid(row=0, column=0, padx=(8, 0), pady=7)

        ctk.CTkLabel(
            top, text="Nyx", font=(FONT, 13, "bold"),
            text_color=C["white"],
        ).grid(row=0, column=1, pady=7)

        # Online dot
        dot = tk.Canvas(top, width=6, height=6, bg=C["card"],
                        highlightthickness=0)
        dot.grid(row=0, column=2, padx=(0, 14), pady=7)
        dot.create_oval(0, 0, 6, 6, fill=C["lime"], outline="")

        # ── Messages ─────────────────────────────────────────────────── #
        self._msgs = ctk.CTkScrollableFrame(
            self, fg_color=C["bg"],
            scrollbar_button_color=C["faint"],
            scrollbar_button_hover_color=C["dim"],
        )
        self._msgs.grid(row=1, column=0, sticky="nsew")
        self._msgs.grid_columnconfigure(0, weight=1)

        # Welcome
        self._bubble(
            "nyx",
            f"Hey {self._uname} 👋\nHow can I help you today?"
        )

        # ── Input bar ────────────────────────────────────────────────── #
        bar = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=52)
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_propagate(False)

        self._entry = ctk.CTkEntry(
            bar, placeholder_text="Message…",
            font=(FONT, 11), height=34,
            fg_color=C["bg"], border_color=C["border"], border_width=1,
            text_color=C["white"], placeholder_text_color=C["faint"],
            corner_radius=17,
        )
        self._entry.grid(row=0, column=0, sticky="ew", padx=(10, 6), pady=9)
        self._entry.bind("<Return>", self._send)

        ctk.CTkButton(
            bar, text="↑", width=34, height=34, corner_radius=17,
            fg_color=C["lime"], hover_color=C["lime_dim"],
            font=(FONT, 15, "bold"), text_color="#000",
            command=self._send,
        ).grid(row=0, column=1, padx=(0, 10), pady=9)

    # ── messages ─────────────────────────────────────────────────────── #

    def _bubble(self, who, text):
        if not self.winfo_exists():
            return
        is_user = who == "user"

        wrap = ctk.CTkFrame(self._msgs, fg_color="transparent")
        wrap.grid(row=self._row, column=0, sticky="ew", padx=6, pady=(4, 0))
        wrap.grid_columnconfigure(0 if is_user else 1, weight=1)

        lbl = ctk.CTkLabel(
            wrap, text=text,
            font=(FONT, 11), text_color=C["white"],
            fg_color=C["bubble_u"] if is_user else C["bubble_n"],
            corner_radius=14, wraplength=220,
            justify="left", anchor="w", padx=12, pady=8,
        )

        if is_user:
            lbl.grid(row=0, column=1, sticky="e", padx=(36, 2))
        else:
            lbl.grid(row=0, column=0, sticky="w", padx=(2, 36))

        self._row += 1
        self._msgs.after(50,
            lambda: self._msgs._parent_canvas.yview_moveto(1.0))

    def _thinking(self):
        if not self.winfo_exists():
            return
        self._think_w = ctk.CTkLabel(
            self._msgs, text="…",
            font=(FONT, 16), text_color=C["faint"],
            anchor="w",
        )
        self._think_w.grid(row=self._row, column=0, sticky="w",
                           padx=10, pady=(4, 0))
        self._row += 1
        self._msgs.after(50,
            lambda: self._msgs._parent_canvas.yview_moveto(1.0))

    def _clear_thinking(self):
        if hasattr(self, "_think_w") and self._think_w.winfo_exists():
            self._think_w.destroy()
            self._row -= 1

    # ── send / receive ───────────────────────────────────────────────── #

    def _send(self, _ev=None):
        text = self._entry.get().strip()
        if not text:
            return
        self._entry.delete(0, "end")
        self._bubble("user", text)

        if self._assistant:
            self._thinking()
            threading.Thread(target=self._ask, args=(text,),
                             daemon=True).start()
        else:
            self._bubble("nyx",
                          "Assistant offline — running in UI-only mode.")

    def _ask(self, text):
        try:
            resp = self._assistant.process_text(text)
        except Exception as e:
            resp = f"Error: {e}"
        self.after(0, self._recv, resp)

    def _recv(self, resp):
        if not self.winfo_exists():
            return
        self._clear_thinking()
        self._bubble("nyx", resp or "No response.")


# ═══════════════════════════════════════════════════════════════════════ #
# APP                                                                     #
# ═══════════════════════════════════════════════════════════════════════ #

class NyxMobileApp:
    """Three-screen launcher: Home · Voice · Chat"""

    W, H = 360, 640

    def __init__(self, user_name: str = "Gaurav"):
        self.user_name = user_name
        self.assistant = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Nyx")
        self.root.geometry(f"{self.W}x{self.H}")
        self.root.minsize(320, 480)
        self.root.configure(fg_color=C["bg"])

        # centre
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(
            f"{self.W}x{self.H}+{(sw-self.W)//2}+{(sh-self.H)//2}")

        self._init_assistant()
        self._screen = None
        self._go_home()

    def _init_assistant(self):
        try:
            from core.assistant import Assistant
            self.assistant = Assistant()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Assistant init: {e}")

    # ── navigation ───────────────────────────────────────────────────── #

    def _swap(self, widget):
        if self._screen:
            self._screen.destroy()
        self._screen = widget
        self._screen.pack(fill="both", expand=True)

    def _go_home(self):
        self._swap(HomeScreen(
            self.root,
            user_name=self.user_name,
            on_voice=self._go_voice,
            on_chat=self._go_chat,
        ))

    def _go_voice(self):
        self._swap(VoiceScreen(self.root, on_back=self._go_home))

    def _go_chat(self):
        self._swap(ChatScreen(
            self.root,
            on_back=self._go_home,
            assistant=self.assistant,
            user_name=self.user_name,
        ))

    def run(self):
        self.root.mainloop()


# Backwards-compatible alias
NyxUI = NyxMobileApp

if __name__ == "__main__":
    NyxMobileApp(user_name="Gaurav").run()
