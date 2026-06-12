# NYX - Local AI Desktop Assistant

Nyx is a fully local, completely free, Jarvis-like desktop AI assistant for Windows. Everything runs on your PC with **NO paid APIs**. Built with Python, Ollama, Whisper, and Piper.

## 🌟 Features

### Phase 1: Voice Assistant MVP ✅
- ✅ Text mode chat interface
- ✅ Voice mode with wake word detection
- ✅ Local LLM (Ollama + Qwen3 4B)
- ✅ Speech-to-text (Whisper)
- ✅ Text-to-speech (Piper)
- ✅ Personality switching
- ✅ Conversation history

### Phase 2: Memory System (Planned)
- Long-term memory with SQLite
- Conversation history management
- User preferences storage
- Project context remembering

### Phase 3: PC Automation (Planned)
- Application launching
- System control (shutdown, restart)
- File operations
- Browser automation

### Phase 4: Screen Understanding (Planned)
- Screenshot analysis
- Code explanation from screen
- Visual element recognition

### Phase 5: Coding Assistant (Planned)
- Code explanation
- Debugging help
- Best practices
- Code generation

### Phase 6: Personalities (Planned)
- Tech Mentor mode
- Friendly Assistant mode
- Gaming Companion mode
- Study Assistant mode

## 🚀 Quick Start

### Prerequisites
- Windows 11
- Python 3.10+
- 8GB RAM
- Internet (for downloading models only)

### 1. Install Ollama
Download and install from: https://ollama.ai

### 2. Download Qwen Model
```powershell
ollama pull qwen:4b
ollama serve
```

### 3. Install Nyx
```powershell
git clone https://github.com/Gaurav-Kanse/Nyx.git
cd Nyx
pip install -r requirements.txt
```

### 4. Run Nyx
```powershell
python main.py
```

## 📁 Project Structure

```
Nyx/
├── core/              # Core assistant logic
│   ├── assistant.py   # Main orchestrator
│   ├── config.py      # Configuration loader
│   └── personality.py # Personality system
├── llm/               # Language model integration
│   ├── ollama_client.py
│   └── prompts.py
├── voice/             # Audio processing
│   ├── stt.py         # Speech-to-text
│   ├── tts.py         # Text-to-speech
│   └── wakeword.py    # Wake word detection
├── ui/                # User interface
│   └── window.py      # CustomTkinter GUI
├── utils/             # Utilities
│   └── logger.py
├── main.py            # Entry point
├── requirements.txt   # Dependencies
└── .env               # Configuration
```

## ⚙️ Configuration

Edit `.env` to customize Nyx:

```env
# LLM Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen:4b

# Speech Recognition (Whisper)
WHISPER_MODEL=base
WHISPER_DEVICE=cpu

# Text-to-Speech (Piper)
PIPER_VOICE=en_US-ryan-high
PIPER_SPEED=1.0

# Wake Word Detection
WAKEWORD_MODEL=hey_google
WAKEWORD_THRESHOLD=0.5

# UI Settings
UI_THEME=dark
UI_WIDTH=600
UI_HEIGHT=700
```

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **LLM** | Ollama + Qwen3 4B | Free, local, efficient |
| **STT** | OpenAI Whisper | Free, accurate, offline |
| **TTS** | Piper | Fast, local, natural |
| **Wake Word** | OpenWakeWord | Free, local detection |
| **Backend** | Python + FastAPI | Lightweight, async |
| **UI** | CustomTkinter | Modern, native feel |
| **Memory** | SQLite | Fast, local, lightweight |
| **Automation** | PyAutoGUI | Cross-platform control |

## 📊 System Requirements

| Metric | Requirement |
|--------|-------------|
| **RAM** | 8GB minimum |
| **Storage** | 5GB for models |
| **CPU** | Any consumer CPU |
| **GPU** | Optional (CPU works fine) |
| **OS** | Windows 11 |
| **Python** | 3.10+ |

## 💾 Performance Targets

| Metric | Target |
|--------|--------|
| **Startup** | <10 seconds |
| **Response** | <5 seconds |
| **Idle RAM** | <500MB |
| **Active RAM** | <2.5GB |
| **STT Speed** | <2 seconds |
| **TTS Speed** | <3 seconds |

## 🎯 Design Philosophy

1. **100% Local**: No cloud, no APIs, no subscriptions
2. **Free**: All components are open-source
3. **Efficient**: Optimized for 8GB RAM consumer hardware
4. **Modular**: Easy to extend and customize
5. **Accessible**: Clear code, good documentation
6. **Privacy**: Your data never leaves your PC

## 🔧 Development Status

- **Phase 1**: ✅ Complete (Voice Assistant MVP)
- **Phase 2**: ⏳ In Progress (Memory System)
- **Phase 3**: 📅 Planned (PC Automation)
- **Phase 4**: 📅 Planned (Screen Understanding)
- **Phases 5-7**: 📅 Planned

## 📖 Documentation

- [Phase 1 Setup Guide](PHASE1_SETUP.md) - Installation & configuration
- [Architecture Guide](ARCHITECTURE.md) - System design & components
- [API Reference](API.md) - Core interfaces (Phase 2+)

## 🤝 Contributing

Contributions welcome! Areas:
- Performance optimization
- Bug fixes
- New personalities
- Automation actions
- UI improvements

## 📝 License

MIT License - See LICENSE file

## 🎓 Learning Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [Piper TTS](https://github.com/rhasspy/piper)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)

## 🚀 Future Vision

Nyx will eventually support:
- Multi-agent system
- Discord bot integration
- Mobile companion app
- Home automation
- Advanced vision capabilities
- RAG with local knowledge base
- Chrome/Edge extensions

---

**Built with ❤️ for privacy, efficiency, and accessibility**

Questions? Check [PHASE1_SETUP.md](PHASE1_SETUP.md) for detailed installation instructions.
