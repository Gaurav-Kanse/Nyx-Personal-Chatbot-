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

class Assistant:
    def __init__(self, personality: str = "default"):
        self.llm = OllamaClient()
        self.stt = WhisperSTT()
        self.tts = PiperTTS()
        self.wakeword = WakeWordDetector()
        self.brain = NyxBrain()
        self.personality = get_personality(personality)
        self.conversation_history = []
        
        logger.info("Assistant initialized.")

    def check_status(self) -> dict:
        """Queries status of local AI engines and service connections."""
        llm_available = self.llm.is_available()
        
        # Check active model
        active_model = "None"
        if llm_available:
            self.llm.refresh_active_model()
            active_model = self.llm.active_model
            
        return {
            "llm": llm_available,
            "active_model": active_model,
            "stt": True,  # Whisper loads lazily, defaults to true
            "tts": True,  # Piper binary check passes if it downloads
            "wakeword": self.wakeword.available,
            "personality": self.personality.name,
            "memory": "Active (Transient)" if Config.ENABLE_MEMORY else "Disabled"
        }

    def process_text(self, user_input: str) -> str:
        """Sends chat request to local Ollama LLM and stores history."""
        # 1. Update brain metrics
        self.brain.set_memory(
            "session_conversations_count", 
            self.brain.get_memory("session_conversations_count", 0) + 1
        )
        
        # 2. Format prompts
        system_prompt = f"{SYSTEM_PROMPT}\n\nPersonality: {self.personality.system_prompt}"

        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Keep history bounded to avoid memory blow-up on 8GB RAM PC (e.g., last 15 messages)
        max_history = 15
        if len(self.conversation_history) > max_history * 2:
            self.conversation_history = self.conversation_history[-max_history * 2:]

        # Call local LLM
        response = self.llm.chat(self.conversation_history, system_prompt=system_prompt)

        if response and not response.startswith("Error:"):
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

        return response

    def speak(self, text: str):
        """Synthesizes and plays back speech."""
        return self.tts.speak(text, play=True)

    def set_personality(self, personality_name: str):
        """Changes assistant personality dynamically."""
        self.personality = get_personality(personality_name)
        logger.info(f"Assistant personality set to: {self.personality.name}")

    def clear_history(self):
        """Resets short term history context."""
        self.conversation_history = []
        logger.info("Conversation history cleared.")

    def get_conversation_history(self) -> list:
        return self.conversation_history
