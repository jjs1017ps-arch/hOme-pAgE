from .tts_interface import TTSInterface
import requests
from loguru import logger

class TTSEngine(TTSInterface):
    def __init__(
        self, 
        api_key: str, 
        voice_id: str, 
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.stability = stability
        self.similarity_boost = similarity_boost
        self.style = style
        self.use_speaker_boost = use_speaker_boost

    def generate_audio(self, text: str, file_name_no_ext=None) -> str:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity_boost,
                "style": self.style,
                "use_speaker_boost": self.use_speaker_boost
            }
        }

        logger.debug(f"Generating audio with ElevenLabs: {text[:20]}...")
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            logger.error(f"ElevenLabs error: {response.text}")
            raise Exception(f"ElevenLabs error: {response.text}")

        file_path = self.generate_cache_file_name(file_name_no_ext, "mp3")
        with open(file_path, "wb") as f:
            f.write(response.content)

        return file_path
