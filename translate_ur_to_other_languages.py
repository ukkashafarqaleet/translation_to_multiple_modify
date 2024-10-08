import pyaudio
import wave
import threading
import os
import time
import openai
import json
import logging
from configparser import RawConfigParser
from datetime import datetime
import sys

api_key = os.getenv("OAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key is not set in environment variables. Please set the OAI_API_KEY environment variable.")

openai.api_key = api_key

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("live_translation.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

translation_conf = sys.argv[1]
config = RawConfigParser()
config.read(translation_conf)

locale_to_language_map_str = config.get("translation_service_config", "locale_to_language_map")
locale_to_language_map = json.loads(locale_to_language_map_str)
speech_to_text_model = config.get("openai_model_config", "speech_to_text_model")  
text_to_text_model = config.get("openai_model_config", "text_to_text_model")  
target_voice_bot = config.get("openai_model_config", "target_voice_bot")  
text_to_text_trans_threshold_in_bytes = int(config.get("openai_model_config", "text_to_text_trans_threshold_in_bytes"))

target_locales = sys.argv[2:6]
process_dir = os.path.join(os.getcwd(), f"live_process_{datetime.utcnow().strftime('%d-%m-%Y-%H-%M-%S')}")


os.makedirs(process_dir, exist_ok=True)
os.chdir(process_dir)

def capture_audio(duration=60, filename="live_input.wav"):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = duration

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print(f"Recording live audio for {duration} seconds...")

    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wave_file = wave.open(filename, 'wb')
    wave_file.setnchannels(CHANNELS)
    wave_file.setsampwidth(p.get_sample_size(FORMAT))
    wave_file.setframerate(RATE)
    wave_file.writeframes(b''.join(frames))
    wave_file.close()

    print(f"Live audio saved as {filename}")
    return filename


def transcribe_audio(file):
    with open(file, "rb") as audio_file:
        transcription = openai.Audio.transcribe(model=speech_to_text_model, file=audio_file)
        return transcription["text"]


def translate_text(text, target_locale):
    target_lang = locale_to_language_map.get(target_locale)
    if not target_lang:
        raise ValueError(f"Locale {target_locale} not supported")
    
    chunk_size = text_to_text_trans_threshold_in_bytes
    sentences = text.split('. ')
    translated_text = []

    chunk = ""
    for sentence in sentences:
        chunk += sentence + ". "
        if len(chunk.encode('utf-8')) >= chunk_size or sentence == sentences[-1]:
            response = openai.ChatCompletion.create(
                messages=[
                    {"role": "system", "content": f"Please translate the following text into {target_lang}"},
                    {"role": "user", "content": chunk}
                ],
                model=text_to_text_model
            )
            translation = response['choices'][0]['message']['content']
            translated_text.append(translation)
            chunk = ""
    
    return "\n".join(translated_text)


def process_live_input(duration):
    audio_file = capture_audio(duration=duration)
    
    log_message = "Transcribing live audio..."
    logger.info(log_message)
    print(log_message)
    
    transcript = transcribe_audio(audio_file)
    print(f"Transcript: {transcript}")
    for locale in target_locales:
        log_message = f"Translating transcript into {locale}..."
        logger.info(log_message)
        print(log_message)

        translation = translate_text(transcript, locale)
        
        target_file = os.path.join(process_dir, f"translation_{locale}.txt")
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(translation)
        
        print(f"Translation for {locale} saved in {target_file}")

if __name__ == "__main__":
    duration = 15  
    process_live_input(duration)