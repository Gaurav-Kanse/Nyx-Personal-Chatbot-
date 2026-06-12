import subprocess
import os
from pathlib import Path
from core.config import Config
from utils.helpers import check_and_setup_piper
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PiperTTS:
    def __init__(self):
        self.speed = Config.PIPER_SPEED
        self.temp_dir = Path(Config.BASE_DIR) / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        self.voice_model_path = None
        self.piper_exe_path = None

    def initialize(self) -> bool:
        """Initializes piper executable and voice. Downloads if missing."""
        try:
            setup_res = check_and_setup_piper(Config.BASE_DIR)
            if setup_res["status"] == "ok":
                self.piper_exe_path = setup_res["piper_exe"]
                self.voice_model_path = setup_res["voice_onnx"]
                logger.info("Piper TTS initialized successfully.")
                return True
            else:
                logger.error(f"Piper TTS initialization failed: {setup_res.get('message')}")
                return False
        except Exception as e:
            logger.error(f"Error initializing Piper: {e}")
            return False

    def speak(self, text: str, play: bool = True) -> str:
        """Synthesizes text to speech and plays it back."""
        if not self.piper_exe_path or not self.voice_model_path:
            logger.info("Piper not pre-initialized, running setup...")
            if not self.initialize():
                return "Error: Piper setup failed"

        try:
            output_file = self.temp_dir / "output.wav"

            # Command to run piper
            cmd = [
                str(self.piper_exe_path),
                "-m", str(self.voice_model_path),
                "-f", str(output_file),
                "--length-scale", str(1.0 / self.speed)
            ]

            logger.info(f"Synthesizing text: '{text[:40]}...'")
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Piper expects text encoded in utf-8, followed by newline
            stdout, stderr = process.communicate(input=(text + "\n").encode("utf-8"))

            if process.returncode != 0:
                err_msg = stderr.decode(errors="ignore")
                logger.error(f"TTS Synthesis error (code {process.returncode}): {err_msg}")
                return f"TTS Error: {err_msg}"

            if play and output_file.exists():
                self.play_audio(str(output_file))

            return str(output_file)

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return f"Error: {str(e)}"

    def play_audio(self, audio_file: str):
        """Plays output WAV file using sounddevice and soundfile."""
        try:
            import sounddevice as sd
            import soundfile as sf

            data, samplerate = sf.read(audio_file)
            sd.play(data, samplerate)
            sd.wait()

        except ImportError:
            logger.error("Error: soundfile or sounddevice not installed in Python.")
        except Exception as e:
            logger.error(f"Audio playback error: {str(e)}")
