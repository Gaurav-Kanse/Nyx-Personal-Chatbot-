import whisper
import numpy as np
import sounddevice as sd
import time
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class WhisperSTT:
    def __init__(self):
        self.model = None
        self.sample_rate = Config.SAMPLE_RATE
        self.device_index = Config.AUDIO_DEVICE_INDEX if Config.AUDIO_DEVICE_INDEX != -1 else None

    def initialize_model(self):
        """Loads the Whisper model on demand to save memory on startup."""
        if self.model is None:
            logger.info(f"Loading Whisper model '{Config.WHISPER_MODEL}' on '{Config.WHISPER_DEVICE}'...")
            self.model = whisper.load_model(Config.WHISPER_MODEL, device=Config.WHISPER_DEVICE)
            logger.info("Whisper model loaded successfully.")

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribes an audio file on disk."""
        try:
            self.initialize_model()
            result = self.model.transcribe(audio_path)
            return result["text"].strip()
        except Exception as e:
            logger.error(f"Error during audio transcription: {e}")
            return f"Error: {str(e)}"

    def transcribe_numpy_array(self, audio_array: np.ndarray) -> str:
        """Transcribes a numpy audio array."""
        try:
            self.initialize_model()
            result = self.model.transcribe(audio=audio_array, language="en")
            return result["text"].strip()
        except Exception as e:
            logger.error(f"Error during numpy transcription: {e}")
            return f"Error: {str(e)}"

    def record_dynamically(self, max_duration: int = 15, silence_limit: float = 1.5, initial_timeout: float = 5.0) -> np.ndarray:
        """
        Records audio dynamically from the microphone.
        Starts when the user speaks (based on calibrated threshold).
        Stops when the user is silent for `silence_limit` seconds.
        """
        chunk_size = 1024
        audio_buffer = []
        
        logger.info("Opening audio stream for recording...")
        
        # Open the input stream
        try:
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=chunk_size,
                device=self.device_index
            )
        except Exception as e:
            logger.error(f"Failed to open microphone: {e}")
            raise RuntimeError(f"Microphone input error: {e}")

        with stream:
            logger.info("Calibrating microphone noise floor (0.3 seconds)...")
            calibration_chunks = []
            for _ in range(int(self.sample_rate * 0.3 / chunk_size)):
                chunk, _ = stream.read(chunk_size)
                calibration_chunks.append(chunk)
            
            # Calibrate threshold: mean energy + buffer, min 0.012
            calib_array = np.concatenate(calibration_chunks)
            noise_floor = np.sqrt(np.mean(calib_array ** 2))
            threshold = max(noise_floor * 1.8, 0.012)
            logger.info(f"Microphone calibrated. Noise floor: {noise_floor:.5f}, Threshold: {threshold:.5f}")

            logger.info("Listening... Speak now.")
            
            speech_started = False
            silence_start_time = None
            start_time = time.time()
            initial_silence_start = time.time()

            while True:
                chunk, _ = stream.read(chunk_size)
                chunk_flat = chunk.squeeze()
                audio_buffer.append(chunk_flat)
                
                # Calculate energy
                rms = np.sqrt(np.mean(chunk_flat ** 2))
                
                current_time = time.time()
                
                # Check for speech activation
                if not speech_started:
                    if rms > threshold:
                        speech_started = True
                        logger.info("Speech detected. Recording...")
                    elif current_time - initial_silence_start > initial_timeout:
                        logger.info("Initial silence timeout. No speech detected.")
                        return np.array([], dtype=np.float32)
                else:
                    # User is speaking, monitor for silence
                    if rms < threshold:
                        if silence_start_time is None:
                            silence_start_time = current_time
                        elif current_time - silence_start_time > silence_limit:
                            logger.info("Silence detected. Stopping recording.")
                            break
                    else:
                        # Reset silence timer when sound is detected
                        silence_start_time = None

                # Check max duration
                if current_time - start_time > max_duration:
                    logger.info("Max recording duration reached.")
                    break

        # Concatenate and return
        if len(audio_buffer) == 0:
            return np.array([], dtype=np.float32)
        return np.concatenate(audio_buffer)

    def transcribe_microphone(self) -> str:
        """Records from mic dynamically and transcribes the output."""
        try:
            audio_data = self.record_dynamically()
            if audio_data.size == 0:
                return ""
            
            logger.info("Transcribing recording...")
            return self.transcribe_numpy_array(audio_data)
        except Exception as e:
            logger.error(f"Microphone transcription failed: {e}")
            return f"Error: {str(e)}"
