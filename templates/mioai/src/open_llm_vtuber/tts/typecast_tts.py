import os
import asyncio
import aiohttp
from loguru import logger
from .tts_interface import TTSInterface

# Global lock to prevent concurrent requests to Typecast API across instances if needed,
# but here it serves to sequence requests from this engine.
_typecast_lock = asyncio.Lock()

class TTSEngine(TTSInterface):
    def __init__(self, api_key: str, actor_id: str, speech_tempo: float = 1.0, audio_format: str = 'mp3', **kwargs):
        self.api_key = api_key.strip()
        self.actor_id = actor_id.strip()
        self.speech_tempo = float(speech_tempo or kwargs.get("speech_tempo", 1.0))
        self.audio_format = audio_format
        
        logger.debug(f"Typecast Init: Actor={self.actor_id}, Tempo={self.speech_tempo}")
        
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        self.new_audio_dir = "cache"
        if not os.path.exists(self.new_audio_dir):
            os.makedirs(self.new_audio_dir)

    def generate_audio(self, text: str, file_name_no_ext: str | None = None) -> str | None:
        try:
            return asyncio.run(self.async_generate_audio(text, file_name_no_ext))
        except RuntimeError:
            logger.error("generate_audio called while event loop is running.")
            return None

    async def async_generate_audio(self, text: str, file_name_no_ext: str | None = None) -> str | None:
        # 1. Acquire lock to ensure we only send ONE request at a time to Typecast
        async with _typecast_lock:
            # Mandatory short sleep to prevent hitting rate limit between sentences
            await asyncio.sleep(0.5)
            
            if not text.endswith(('.', '!', '?')):
                text += '.'
                
            logger.debug(f"🎤 [Typecast v1] Requesting: {text[:30]}... (Tempo: {self.speech_tempo})")

            ext = self.audio_format if self.audio_format else "mp3"
            file_name = os.path.join(self.new_audio_dir, f"{file_name_no_ext}.{ext}" if file_name_no_ext else f"test.{ext}")

            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": text,
                    "voice_id": self.actor_id,
                    "model": "ssfm-v21",
                    "model_version": "latest",
                    "config": {
                        "tempo": self.speech_tempo,
                        "audio_format": self.audio_format
                    }
                }

                # 2. Implementation with automatic retry for Rate Limit (429)
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        async with session.post('https://api.typecast.ai/v1/text-to-speech', headers=self.headers, json=payload) as resp:
                            if resp.status == 429:
                                wait_time = (attempt + 1) * 2
                                logger.warning(f"⚠️ Typecast Rate Limit hit. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                                await asyncio.sleep(wait_time)
                                continue

                            if resp.status != 200 and resp.status != 201:
                                error_msg = await resp.text()
                                logger.error(f"Typecast v1 POST Error (status {resp.status}): {error_msg}")
                                return None

                            content_type = resp.headers.get('Content-Type', '')
                            
                            # Direct Audio Response
                            if 'audio' in content_type:
                                audio_bytes = await resp.read()
                                with open(file_name, "wb") as f:
                                    f.write(audio_bytes)
                                logger.success(f"✨ Typecast audio generated (Direct): {file_name}")
                                return file_name

                            # JSON Polling Response
                            data = await resp.json()
                            result_data = data.get('result', {})
                            poll_url = result_data.get('status_url') or data.get('status_url')
                            
                            if not poll_url:
                                download_url = result_data.get('audio_download_url') or data.get('audio_download_url')
                                if not download_url:
                                    logger.error(f"Unexpected Typecast response: {data}")
                                    return None
                            else:
                                # 3. Polling Logic
                                download_url = None
                                for i in range(60):
                                    await asyncio.sleep(1)
                                    async with session.get(poll_url, headers=self.headers) as poll_resp:
                                        if poll_resp.status != 200: continue
                                        poll_data = await poll_resp.json()
                                        result = poll_data.get('result', poll_data)
                                        if result.get('status') in ['done', 'DONE']:
                                            download_url = result.get('audio_download_url')
                                            break
                                        elif result.get('status') in ['failed', 'FAILED']:
                                            logger.error(f"Typecast generation failed: {result}")
                                            return None
                                
                                if not download_url: return None

                            # 4. Final Download
                            async with session.get(download_url) as dl_resp:
                                if dl_resp.status == 200:
                                    audio_bytes = await dl_resp.read()
                                    with open(file_name, "wb") as f:
                                        f.write(audio_bytes)
                                    logger.success(f"✨ Typecast audio generated (Polled): {file_name}")
                                    return file_name
                                
                            break # Success, exit retry loop

                    except Exception as e:
                        logger.exception(f"Error during Typecast TTS: {e}")
                        break

        return None
