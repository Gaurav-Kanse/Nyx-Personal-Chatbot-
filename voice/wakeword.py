import numpy as np
import sounddevice as sd
import time
from pathlib import Path
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class WakeWordDetector:
    def __init__(self):
        self.model = None
        self.available = False
        self.threshold = Config.WAKEWORD_THRESHOLD
        self.sample_rate = 16000  # openwakeword strictly expects 16kHz
        self.chunk_size = 1280    # openwakeword strictly expects 1280 samples (80ms)
        self.device_index = Config.AUDIO_DEVICE_INDEX if Config.AUDIO_DEVICE_INDEX != -1 else None
        
        try:
            from openwakeword.model import Model
            
            # Locate custom model path or default
            models_dir = Path(Config.BASE_DIR) / "data" / "models"
            custom_model_path = models_dir / f"{Config.WAKEWORD_MODEL}.onnx"
            
            if custom_model_path.exists():
                logger.info(f"Loading custom wake word model from {custom_model_path}")
                self.model = Model(wakeword_models=[str(custom_model_path)])
                self.model_name = Config.WAKEWORD_MODEL
            else:
                # Fall back to built-in openwakeword model (e.g. hey_google, alexa, jarvis)
                logger.info(f"Loading built-in wake word model '{Config.WAKEWORD_MODEL}'")
                self.model = Model(wakeword_models=[Config.WAKEWORD_MODEL])
                self.model_name = Config.WAKEWORD_MODEL
                
            self.available = True
            logger.info("OpenWakeWord detector loaded successfully.")
        except ImportError:
            logger.warning("OpenWakeWord Python package not installed. Wake word detection is disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize openwakeword model: {e}")

    def detect_from_microphone(self, timeout: float = 30.0, stop_flag=None) -> bool:
        """
        Listens to the microphone and blocks until the wake word is detected
        or the timeout is reached.
        """
        if not self.available or self.model is None:
            logger.warning("Wake word detection is not initialized.")
            time.sleep(2)  # avoid tight loops if called in background
            return False

        logger.info(f"Listening for wake word '{self.model_name}' (timeout: {timeout}s)...")
        start_time = time.time()
        
        try:
            # Open stream in int16, 1 channel, 16000Hz, blocksize 1280
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.int16,
                blocksize=self.chunk_size,
                device=self.device_index
            )
        except Exception as e:
            logger.error(f"Wake word input stream failed: {e}")
            return False

        # Reset model states before starting new detection loop
        self.model.reset()

        with stream:
            while True:
                # Check external stop flag
                if stop_flag and stop_flag():
                    logger.info("Wake word listener stopped externally.")
                    return False
                    
                # Check timeout
                if time.time() - start_time > timeout:
                    logger.info("Wake word listening timed out.")
                    return False

                # Read audio chunk
                try:
                    audio_chunk, _ = stream.read(self.chunk_size)
                    audio_chunk = audio_chunk.squeeze()
                except Exception as e:
                    logger.error(f"Error reading chunk from stream: {e}")
                    time.sleep(0.1)
                    continue

                if audio_chunk.shape[0] != self.chunk_size:
                    continue

                # Run prediction
                try:
                    prediction = self.model.predict(audio_chunk)
                    
                    # Search for our wake word's score in prediction dict
                    for model_key, score in prediction.items():
                        if self.model_name in model_key or model_key == self.model_name:
                            if score > self.threshold:
                                logger.info(f"Wake word '{self.model_name}' detected! Score: {score:.3f}")
                                return True
                except Exception as e:
                    logger.error(f"Error during wake word prediction: {e}")
                    
        return False
