import os
from gtts import gTTS
from config import Config


def synthesize_text(text, filename="tts_response.mp3"):
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    safe_filename = os.path.join(Config.UPLOAD_FOLDER, filename)
    tts = gTTS(text=text, lang="en")
    tts.save(safe_filename)
    return safe_filename


def get_tts_message(text, filename="tts_response.mp3"):
    filepath = synthesize_text(text, filename)
    return {
        "message": text,
        "audio_url": f"/{filepath.replace('\\', '/')}",
    }
