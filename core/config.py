import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent

    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen:4b")

    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")

    PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-ryan-high")
    PIPER_SPEED = float(os.getenv("PIPER_SPEED", "1.0"))

    WAKEWORD_MODEL = os.getenv("WAKEWORD_MODEL", "hey_google")
    WAKEWORD_THRESHOLD = float(os.getenv("WAKEWORD_THRESHOLD", "0.5"))

    AUDIO_DEVICE_INDEX = int(os.getenv("AUDIO_DEVICE_INDEX", "-1"))
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2048"))

    UI_THEME = os.getenv("UI_THEME", "dark")
    UI_WIDTH = int(os.getenv("UI_WIDTH", "600"))
    UI_HEIGHT = int(os.getenv("UI_HEIGHT", "700"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.path.join(BASE_DIR, os.getenv("LOG_FILE", "logs/nyx.log"))

    ENABLE_VOICE = os.getenv("ENABLE_VOICE", "true").lower() == "true"
    ENABLE_TEXT = os.getenv("ENABLE_TEXT", "true").lower() == "true"
    ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() == "true"
    ENABLE_CODING = os.getenv("ENABLE_CODING", "false").lower() == "true"
    ENABLE_AUTOMATION = os.getenv("ENABLE_AUTOMATION", "true").lower() == "true"
    AUTOMATION_CONFIRM_DESTRUCTIVE = os.getenv("AUTOMATION_CONFIRM_DESTRUCTIVE", "true").lower() == "true"
