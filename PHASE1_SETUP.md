# Nyx Phase 1: Voice Assistant MVP - Setup & Installation Guide

## Overview

This is Phase 1 of Nyx: a fully local, completely free, Jarvis-like desktop AI assistant. All components run on your PC with NO paid APIs.

## Architecture Components

### Core Modules

| Module | Purpose | File |
|--------|---------|------|
| **LLM** | Ollama client for local LLM inference | `llm/ollama_client.py` |
| **STT** | OpenAI Whisper for speech-to-text | `voice/stt.py` |
| **TTS** | Piper for text-to-speech | `voice/tts.py` |
| **Wake Word** | OpenWakeWord for "Hey Google" detection | `voice/wakeword.py` |
| **Assistant** | Main orchestrator connecting all components | `core/assistant.py` |
| **UI** | CustomTkinter-based chat interface | `ui/window.py` |
| **Config** | Configuration loader from .env | `core/config.py` |
| **Personality** | Personality switching system | `core/personality.py` |

## Installation Steps

### Step 1: Install Ollama

Ollama is the LLM runtime. Download and install from: https://ollama.ai

1. Download Ollama for Windows
2. Install it
3. Open PowerShell and verify installation:
   ```powershell
   ollama --version
   ```

### Step 2: Download Qwen3 4B Model

Open PowerShell and run:
```powershell
ollama pull qwen:4b
```

This will download the 4B parameter Qwen model (~2.4GB). This is optimized for 8GB RAM systems.

### Step 3: Start Ollama Server

```powershell
ollama serve
```

Keep this terminal open. Ollama will listen on `http://localhost:11434`

### Step 4: Install Python Dependencies

Open another PowerShell terminal in the Nyx directory and run:

```powershell
pip install -r requirements.txt
```

This installs:
- **fastapi** - Web framework (not used in Phase 1 but prepared for Phase 2)
- **customtkinter** - Modern GUI framework
- **torch** - PyTorch for ML models
- **whisper** - Speech recognition
- **sounddevice** - Audio input/output
- **piper-tts** - Text-to-speech
- **openwakeword** - Wake word detection
- **python-dotenv** - Environment configuration

### Step 5: Install System Tools

#### Piper (Text-to-Speech)

Windows binary download: https://github.com/rhasspy/piper/releases

1. Download `piper_windows_amd64.zip`
2. Extract it
3. Add to PATH or note the executable location
4. Verify installation:
   ```powershell
   piper --version
   ```

#### OpenWakeWord (Optional for Phase 1)

Already installed via pip. Supports "Hey Google" wake word detection.

### Step 6: Verify Installation

Run this Python script to check all components:

```python
from llm.ollama_client import OllamaClient
from voice.stt import WhisperSTT
from voice.tts import PiperTTS
from voice.wakeword import WakeWordDetector

print("Checking Ollama...")
llm = OllamaClient()
print(f"✓ Ollama: {llm.is_available()}")

print("Checking Whisper...")
stt = WhisperSTT()
print("✓ Whisper loaded")

print("Checking Piper...")
tts = PiperTTS()
print("✓ Piper ready")

print("Checking OpenWakeWord...")
wwd = WakeWordDetector()
print(f"✓ Wake Word: {wwd.available}")

print("\n✓ All systems ready!")
```

### Step 7: Run Nyx

From the Nyx directory:

```powershell
python main.py
```

## Configuration (.env file)

The `.env` file controls all settings:

```env
# Ollama LLM settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen:4b

# Whisper STT settings
WHISPER_MODEL=base          # Options: tiny, base, small, medium, large
WHISPER_DEVICE=cpu          # Use 'cuda' if you have NVIDIA GPU

# Piper TTS settings
PIPER_VOICE=en_US-ryan-high # Multiple voices available
PIPER_SPEED=1.0             # 0.5 (slow) to 2.0 (fast)

# Wake word settings
WAKEWORD_MODEL=hey_google   # Wake word to detect
WAKEWORD_THRESHOLD=0.5      # Detection sensitivity (0.0-1.0)

# Audio settings
SAMPLE_RATE=16000
CHUNK_SIZE=2048
```

## Features in Phase 1

✅ **Text Mode**
- Type messages
- Nyx responds using Ollama LLM
- Optional text-to-speech output
- Conversation history

✅ **Voice Mode** (Basic)
- Wake word detection button
- Speech-to-text with Whisper
- LLM processing
- Text-to-speech response

✅ **Personality System**
- Switch between personalities
- Default, Friendly, Tech Mentor, Gaming modes
- System prompt changes per personality

✅ **UI**
- Modern dark theme
- Chat display
- Text input field
- Voice button
- Personality selector
- Clear chat button
- Status indicators

## Testing the System

### Test 1: Text Mode
1. Run `python main.py`
2. Type: "Hello, what is your name?"
3. Nyx responds with conversation

### Test 2: Personality Switching
1. Type: "Switch to friendly mode"
2. Select "friendly" from dropdown
3. Type: "Hey, what's up?"
4. Notice the tone changes

### Test 3: Voice Mode (if microphone available)
1. Click the "🎤 Voice" button
2. Wait for wake word listening
3. Say "Hey Google"
4. Speak your question
5. Nyx responds

## System Requirements

- **RAM**: 8GB minimum (targeting <3GB during use)
- **Storage**: 5GB for models (Ollama 2.4GB + Whisper 1.5GB)
- **Processor**: Any CPU (optimized for consumer hardware)
- **Audio**: Microphone and speaker (USB adapters OK)
- **Internet**: Only needed for initial model downloads

## Performance Targets - Phase 1

| Metric | Target | Notes |
|--------|--------|-------|
| **Startup Time** | <10 seconds | UI loads quickly |
| **Response Time** | <5 seconds | Ollama inference |
| **STT Latency** | <2 seconds | Whisper processing |
| **TTS Latency** | <3 seconds | Piper synthesis |
| **Idle RAM** | <500MB | UI only |
| **Active RAM** | <2.5GB | All components active |

## Troubleshooting

### Ollama Connection Error
- Ensure Ollama is running: `ollama serve`
- Check connection: `curl http://localhost:11434/api/tags`
- Port 11434 not blocked by firewall

### Whisper Slow
- First run downloads model (~140MB)
- Subsequent runs are faster
- Use `tiny` or `base` model (already set)

### Piper TTS Not Working
- Verify Piper is in PATH: `piper --version`
- Or specify full path in code
- Install FFmpeg if audio playback fails

### Wake Word Not Detecting
- Check microphone in Windows Settings
- Verify audio device index: `python -c "import sounddevice; print(sounddevice.query_devices())"`
- Adjust WAKEWORD_THRESHOLD in .env (lower = more sensitive)

### High RAM Usage
- Use smaller Whisper model: `WHISPER_MODEL=tiny`
- Reduce chat history (implemented in Phase 2)
- Close other applications

## Next Steps

Phase 1 is now complete! Ready for:

- **Phase 2**: Memory System (SQLite, long-term memory)
- **Phase 3**: PC Automation (app launching, file operations)
- **Phase 4**: Screen Understanding (vision capabilities)
- **Phase 5**: Coding Assistant (specialized prompts)
- **Phase 6**: Personality Expansion
- **Phase 7**: Optimization & Multi-agent System

## Key Design Decisions - Phase 1

1. **Qwen 4B over larger models**: Fits in 8GB RAM, still highly capable
2. **Whisper Base**: Good accuracy/speed trade-off for CPU
3. **Piper TTS**: Fast, local, no network needed
4. **CustomTkinter**: Lightweight, modern, Windows-native feel
5. **FastAPI prepared**: Ready for Phase 2 REST API
6. **Modular architecture**: Easy to add features in future phases

## Code Quality Notes

- Production-ready code (no placeholders)
- Error handling for all external calls
- Graceful degradation if components unavailable
- Clean separation of concerns
- Configuration-driven behavior
- Thread-safe operations
- Comprehensive logging

---

**Status**: Phase 1 MVP complete and ready for testing!
