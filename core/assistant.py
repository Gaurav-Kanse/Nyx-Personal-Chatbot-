"""
core/assistant.py
Nyx Assistant — orchestrates LLM, voice pipeline, persistent memory, and PC automation.
"""

from typing import Optional
from llm.ollama_client import OllamaClient
from llm.prompts import SYSTEM_PROMPT
from voice.stt import WhisperSTT
from voice.tts import PiperTTS
from voice.wakeword import WakeWordDetector
from core.personality import get_personality, Personality
from core.brain import NyxBrain
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

COMMAND_PREFIX = "/"

# ---------------------------------------------------------------------------
# Automation — lazy-loaded so voice/memory start instantly even if psutil
# isn't installed yet.
# ---------------------------------------------------------------------------
_registry = None
_router   = None

def _get_automation():
    global _registry, _router
    if _registry is None and Config.ENABLE_AUTOMATION:
        try:
            from automation.registry import build_registry
            from automation.router   import AutomationRouter
            _registry = build_registry()
            _router   = AutomationRouter(_registry)
            logger.info("Automation subsystem loaded.")
        except Exception as exc:
            logger.warning(f"Automation subsystem unavailable: {exc}")
    return _registry, _router


class Assistant:
    def __init__(self, personality: str = "default"):
        self.llm         = OllamaClient()
        self.stt         = WhisperSTT()
        self.tts         = PiperTTS()
        self.wakeword    = WakeWordDetector()
        self.brain       = NyxBrain()
        self.personality = get_personality(personality)
        self.conversation_history = []

        # Eagerly init automation on startup (non-blocking on import errors)
        _get_automation()

        logger.info("Assistant initialized.")

    # ------------------------------------------------------------------ #
    # STATUS                                                               #
    # ------------------------------------------------------------------ #

    def check_status(self) -> dict:
        llm_available = self.llm.is_available()
        active_model  = "None"
        if llm_available:
            self.llm.refresh_active_model()
            active_model = self.llm.active_model

        registry, _ = _get_automation()
        tool_count   = len(registry.list_tools()) if registry else 0

        return {
            "llm":          llm_available,
            "active_model": active_model,
            "stt":          True,
            "tts":          True,
            "wakeword":     self.wakeword.available,
            "personality":  self.personality.name,
            "memory":       "Active (SQLite)" if Config.ENABLE_MEMORY else "Disabled",
            "automation":   f"Active ({tool_count} tools)" if tool_count else "Disabled",
            "user_name":    self.brain.get_user_name(),
        }

    # ------------------------------------------------------------------ #
    # SLASH-COMMAND HANDLER                                                #
    # ------------------------------------------------------------------ #

    def handle_command(self, text: str) -> Optional[str]:
        """
        Routes /slash commands — memory commands first, then automation.

        Memory commands:
            /name, /notes, /note, /delnote, /memory, /clear, /help

        Automation slash commands (delegated to AutomationRouter):
            /open, /close, /apps, /volume, /mute, /search, /youtube, /url,
            /copy, /paste, /clipboard, /type, /hotkey, /screenshot,
            /file, /ls, /shutdown, /restart, /sleep, /lock
        """
        parts = text.strip().split(maxsplit=1)
        cmd   = parts[0].lower()
        arg   = parts[1].strip() if len(parts) > 1 else ""

        # ── Memory commands ──────────────────────────────────────────── #
        if cmd == "/name":
            if not arg:
                return f"Your current name is **{self.brain.get_user_name()}**. Use `/name <name>` to change it."
            self.brain.set_user_name(arg)
            return f"Got it! I'll call you **{arg}** from now on."

        elif cmd == "/notes":
            notes = self.brain.get_notes()
            if not notes:
                return "No saved notes yet. Use `/note Title|Content` to add one."
            lines = ["**Your Notes:**"]
            for n in notes:
                lines.append(f"  [{n.id}] **{n.title}** ({n.category})\n    {n.content[:80]}…")
            return "\n".join(lines)

        elif cmd == "/note":
            if "|" not in arg:
                return "Usage: `/note Title|Content`"
            title, content = arg.split("|", 1)
            note = self.brain.add_note(title.strip(), content.strip())
            return f"Note saved! [#{note.id}] **{note.title}**"

        elif cmd == "/delnote":
            if not arg.isdigit():
                return "Usage: `/delnote <id>`"
            deleted = self.brain.delete_note(int(arg))
            return f"Note #{arg} deleted." if deleted else f"Note #{arg} not found."

        elif cmd == "/memory":
            ctx = self.brain.build_memory_context()
            return f"**Nyx's memory:**\n{ctx}" if ctx else "No persistent memory stored yet."

        elif cmd == "/clear":
            self.clear_history()
            return "Conversation history cleared."

        elif cmd == "/help":
            return (
                "**Memory commands:**\n"
                "  `/name <value>`        — Set your name\n"
                "  `/note Title|Content`  — Save a note\n"
                "  `/notes`               — List notes\n"
                "  `/delnote <id>`        — Delete a note\n"
                "  `/memory`              — View stored memory\n"
                "  `/clear`               — Clear chat history\n\n"
                "**Automation commands:**\n"
                "  `/open <app>`          — Launch an application\n"
                "  `/close <app>`         — Close an application\n"
                "  `/apps`                — List running processes\n"
                "  `/volume <0-100|up|down|mute>` — Control volume\n"
                "  `/search <query>`      — Web search (DuckDuckGo)\n"
                "  `/youtube <query>`     — YouTube search\n"
                "  `/url <url>`           — Open a URL\n"
                "  `/copy <text>`         — Copy text to clipboard\n"
                "  `/clipboard`           — Read clipboard\n"
                "  `/type <text>`         — Type into focused window\n"
                "  `/hotkey <combo>`      — Press key combo (e.g. ctrl+c)\n"
                "  `/screenshot`          — Take a screenshot\n"
                "  `/file <path>`         — Open file/folder in Explorer\n"
                "  `/ls <path>`           — List directory contents\n"
                "  `/lock`                — Lock screen\n"
                "  `/sleep`               — Sleep PC\n"
                "  `/shutdown`            — Shutdown (asks for confirmation)\n"
                "  `/restart`             — Restart (asks for confirmation)\n"
            )

        # ── Automation slash commands ────────────────────────────────── #
        _, router = _get_automation()
        if router:
            result = router.route_slash(cmd, arg)
            if result is not None:
                return result.message

        return None  # Not handled → pass to LLM

    # ------------------------------------------------------------------ #
    # MAIN TEXT PROCESSOR                                                  #
    # ------------------------------------------------------------------ #

    def process_text(self, user_input: str) -> str:
        # 1. Slash-command interception
        if user_input.startswith(COMMAND_PREFIX):
            response = self.handle_command(user_input)
            if response is not None:
                return response

        # 2. Natural-language automation routing (before LLM)
        if Config.ENABLE_AUTOMATION:
            _, router = _get_automation()
            if router:
                result = router.route(user_input)
                if result is not None:
                    if Config.ENABLE_MEMORY:
                        self.brain.log_user_message(user_input)
                        self.brain.log_assistant_message(result.message)
                    return result.message

        # 3. Log to persistent memory
        if Config.ENABLE_MEMORY:
            self.brain.log_user_message(user_input)
        else:
            self.brain.set_memory(
                "session_conversations_count",
                self.brain.get_memory("session_conversations_count", 0) + 1,
            )

        # 4. Build memory-aware system prompt
        user_name  = self.brain.get_user_name()
        memory_ctx = self.brain.build_memory_context() if Config.ENABLE_MEMORY else ""

        # Include tool descriptions and instructions so LLM can invoke them
        registry, _ = _get_automation()
        tool_ctx = ""
        if registry:
            tool_ctx = (
                f"\n\n{registry.tool_summary()}\n\n"
                "IMPORTANT: If you need to perform any of the automation actions above to satisfy the user's request, "
                "you MUST output ONLY the corresponding slash command (e.g., `/open notepad`, `/volume 50`, `/screenshot`, "
                "`/file C:\\`, `/search cats`) on a single line with NO other text or explanation. "
                "The system will execute it and show the user the result."
            )

        system_prompt = "\n\n".join(filter(None, [
            SYSTEM_PROMPT,
            f"Personality: {self.personality.system_prompt}",
            f"The user's name is {user_name}. Address them by name naturally.",
            memory_ctx,
            tool_ctx,
        ]))

        # 5. Rolling conversation history (bounded for 8GB RAM)
        self.conversation_history.append({"role": "user", "content": user_input})
        max_pairs = 15
        if len(self.conversation_history) > max_pairs * 2:
            self.conversation_history = self.conversation_history[-(max_pairs * 2):]

        # 6. LLM call
        response = self.llm.chat(self.conversation_history, system_prompt=system_prompt)

        # Intercept LLM-generated slash commands
        if response and response.strip().startswith(COMMAND_PREFIX):
            cmd = response.strip().splitlines()[0].strip()
            logger.info(f"LLM generated a slash command: {cmd}")
            cmd_result = self.handle_command(cmd)
            if cmd_result is not None:
                self.conversation_history.append({"role": "assistant", "content": cmd_result})
                if Config.ENABLE_MEMORY:
                    self.brain.log_assistant_message(cmd_result)
                return cmd_result

        # 7. Store assistant reply
        if response and not response.startswith("Error:"):
            self.conversation_history.append({"role": "assistant", "content": response})
            if Config.ENABLE_MEMORY:
                self.brain.log_assistant_message(response)

        return response

    # ------------------------------------------------------------------ #
    # VOICE                                                                #
    # ------------------------------------------------------------------ #

    def speak(self, text: str):
        return self.tts.speak(text, play=True)

    # ------------------------------------------------------------------ #
    # PERSONALITY                                                          #
    # ------------------------------------------------------------------ #

    def set_personality(self, personality_name: str):
        self.personality = get_personality(personality_name)
        logger.info(f"Personality set to: {self.personality.name}")

    # ------------------------------------------------------------------ #
    # HISTORY                                                              #
    # ------------------------------------------------------------------ #

    def clear_history(self):
        self.conversation_history = []
        logger.info("Conversation history cleared.")

    def get_conversation_history(self) -> list:
        return self.conversation_history
