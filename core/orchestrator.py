import threading
import time
import numpy as np
import sounddevice as sd
from typing import Callable
from core.config import Config
from core.assistant import Assistant
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NyxOrchestrator:
    def __init__(self, assistant: Assistant):
        self.assistant = assistant
        self.mic_mode = "muted"  # Options: 'muted', 'ptt', 'wakeword'
        self.state = "IDLE"      # Options: 'IDLE', 'LISTENING_WAKEWORD', 'LISTENING_SPEECH', 'PROCESSING_LLM', 'SPEAKING'
        
        # Callbacks to update UI
        self.state_callback: Callable[[str], None] = lambda s: None
        self.chat_callback: Callable[[str, str], None] = lambda sender, text: None
        
        self.stop_event = threading.Event()
        self.worker_thread = None
        
    def start(self, state_callback: Callable[[str], None], chat_callback: Callable[[str, str], None]):
        """Starts the background audio processing loop."""
        self.state_callback = state_callback
        self.chat_callback = chat_callback
        self.stop_event.clear()
        
        self.worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self.worker_thread.start()
        logger.info("Orchestrator background threads started.")

    def stop(self):
        """Stops the background worker thread."""
        self.stop_event.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
        logger.info("Orchestrator threads stopped.")

    def set_mic_mode(self, mode: str):
        """Sets the microphone input mode ('muted', 'ptt', 'wakeword')."""
        if mode not in ["muted", "ptt", "wakeword"]:
            raise ValueError(f"Invalid mic mode: {mode}")
        
        logger.info(f"Microphone mode changed to: {mode.upper()}")
        self.mic_mode = mode
        
        # Reset state back to IDLE when muting
        if mode == "muted":
            self._update_state("IDLE")

    def play_chime(self, frequency=600, duration=0.12):
        """Plays a gentle high-tech beep to signal listening state."""
        try:
            sr = 16000
            t = np.linspace(0, duration, int(sr * duration), False)
            fade_out = np.linspace(1.0, 0.0, len(t))
            wave = np.sin(2 * np.pi * frequency * t) * 0.25 * fade_out
            
            # play audio buffer directly via sounddevice
            sd.play(wave, sr)
            sd.wait()
        except Exception as e:
            logger.error(f"Chime playback error: {e}")

    def _update_state(self, new_state: str):
        """Updates internal state and fires the UI callback."""
        self.state = new_state
        self.state_callback(new_state)

    def _run_worker(self):
        """Background loop monitoring wake words or push-to-talk requests."""
        while not self.stop_event.is_set():
            try:
                if self.mic_mode == "wakeword":
                    self._update_state("LISTENING_WAKEWORD")
                    # Wait for wake word with a 2-second timeout to check loop flag regularly
                    detected = self.assistant.wakeword.detect_from_microphone(
                        timeout=2.0, 
                        stop_flag=lambda: self.stop_event.is_set() or self.mic_mode != "wakeword"
                    )
                    
                    if detected and self.mic_mode == "wakeword":
                        self._process_voice_interaction()
                        
                elif self.mic_mode == "ptt":
                    # Single trigger voice interaction
                    self._process_voice_interaction()
                    # Automatically revert to muted state after completion
                    self.set_mic_mode("muted")
                    
                else:
                    # Muted or idle: sleep to conserve CPU cycles
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in orchestrator loop: {e}")
                time.sleep(0.5)

    def _process_voice_interaction(self):
        """Records voice, transcribes it, queries LLM, and plays audio TTS."""
        logger.info("Starting voice processing pipeline.")
        
        # 1. Alert user to start speaking
        self.play_chime()
        
        # 2. Record speech
        self._update_state("LISTENING_SPEECH")
        try:
            audio_data = self.assistant.stt.record_dynamically(
                max_duration=15,
                silence_limit=1.5,
                initial_timeout=4.0
            )
        except Exception as e:
            logger.error(f"Speech recording failed: {e}")
            self.chat_callback("System", f"Microphone error: {e}")
            self._update_state("IDLE")
            return
            
        if audio_data.size == 0:
            logger.info("Voice interaction aborted: No speech detected.")
            self._update_state("IDLE")
            return
            
        # 3. Transcribe speech
        self.state_callback("Transcribing...")
        text = self.assistant.stt.transcribe_numpy_array(audio_data)
        
        if not text or text.strip() == "":
            logger.info("Voice interaction aborted: Empty transcription.")
            self._update_state("IDLE")
            return
            
        self.chat_callback("You", text)
        
        # 4. Generate LLM Response
        self.state_callback("Thinking...")
        response = self.assistant.process_text(text)
        
        if not response:
            self._update_state("IDLE")
            return
            
        self.chat_callback("Nyx", response)
        
        # 5. Playback via TTS
        if Config.ENABLE_VOICE and response:
            self._update_state("SPEAKING")
            self.assistant.speak(response)
            
        # 6. Back to IDLE
        self._update_state("IDLE")

    def process_text_async(self, user_text: str):
        """Processes typed text requests in a background thread."""
        def _run():
            self._update_state("PROCESSING_LLM")
            self.state_callback("Thinking...")
            self.chat_callback("You", user_text)
            
            response = self.assistant.process_text(user_text)
            if response:
                self.chat_callback("Nyx", response)
                if Config.ENABLE_VOICE:
                    self._update_state("SPEAKING")
                    self.assistant.speak(response)
            
            self._update_state("IDLE")
            
        threading.Thread(target=_run, daemon=True).start()
