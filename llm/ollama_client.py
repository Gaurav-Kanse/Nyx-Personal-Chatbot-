import requests
import json
from typing import Optional, List, Dict
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class OllamaClient:
    def __init__(self):
        self.host = Config.OLLAMA_HOST
        self.config_model = Config.OLLAMA_MODEL
        self.base_url = f"{self.host}/api"
        self.active_model = self.config_model
        self._model_resolved = False
        self.refresh_active_model()

    def is_available(self) -> bool:
        """Checks if the Ollama service is running."""
        try:
            response = requests.get(f"{self.base_url}/tags", timeout=3)
            return response.status_code == 200
        except:
            return False

    def get_pulled_models(self) -> List[str]:
        """Returns a list of all locally pulled model names from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/tags", timeout=3)
            if response.status_code == 200:
                data = response.json()
                return [m.get("name") for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to query Ollama tags: {e}")
        return []

    def refresh_active_model(self) -> str:
        """
        Verifies if the configured model is available.
        Falls back to another local model if the configured one is not pulled.
        """
        if self._model_resolved:
            return self.active_model

        pulled = self.get_pulled_models()
        if not pulled:
            # Service offline or no models
            self.active_model = self.config_model
            return self.active_model

        # Normalize comparison
        config_lower = self.config_model.lower()
        
        # Check for exact or fuzzy match
        for model in pulled:
            model_lower = model.lower()
            if config_lower == model_lower or config_lower in model_lower or model_lower in config_lower:
                self.active_model = model
                self._model_resolved = True
                logger.info(f"Configured model '{self.config_model}' is available as '{self.active_model}'.")
                return self.active_model

        # Fallback to first available model
        self.active_model = pulled[0]
        self._model_resolved = True
        logger.warning(
            f"Configured model '{self.config_model}' not found in Ollama. "
            f"Falling back to active model: '{self.active_model}'."
        )
        return self.active_model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            self.refresh_active_model()
            payload = {
                "model": self.active_model,
                "prompt": prompt,
                "stream": False,
                "system": system_prompt or ""
            }

            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                return f"Error: Ollama returned status code {response.status_code}"

        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Ensure it's running locally."
        except Exception as e:
            return f"Error: {str(e)}"

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        try:
            self.refresh_active_model()
            payload = {
                "model": self.active_model,
                "messages": messages,
                "stream": False,
                "system": system_prompt or ""
            }

            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "").strip()
            else:
                return f"Error: Ollama returned status code {response.status_code}"

        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Ensure it is running."
        except Exception as e:
            return f"Error: {str(e)}"
