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

# Check if API key is set
api_key = os.getenv("OAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key is not set in environment variables. Please set the OAI_API_KEY environment variable.")

openai.api_key = api_key

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("live_translation.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Read configuration from the provided file
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

def capture_audio_chunk(filename="live_input_chunk.wav", duration=15):
    """Capture a chunk of audio for the given duration."""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print(f"Recording live audio chunk for {duration} seconds...")

    frames = []
    for i in range(0, int(RATE / CHUNK * duration)):
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

    print(f"Live audio chunk saved as {filename}")
    return filename


def transcribe_audio(file):
    """Transcribe the recorded audio file using OpenAI."""
    with open(file, "rb") as audio_file:
        transcription = openai.Audio.transcribe(model=speech_to_text_model, file=audio_file)
        return transcription["text"]


def translate_text(text, target_locale):
    """Translate the given text to the specified locale."""
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


def process_audio_chunk():
    """Capture, transcribe, and translate an audio chunk."""
    audio_file = capture_audio_chunk()
    
    log_message = "Transcribing audio chunk..."
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
        with open(target_file, 'a', encoding='utf-8') as f:
            f.write(translation + "\n")

        print(f"Translation for {locale} saved in {target_file}")


def continuous_translation():
    """Continuously capture, transcribe, and translate audio in chunks."""
    try:
        while True:
            process_audio_chunk()
            time.sleep(1)  # Sleep for 1 second between each 15-second audio chunk
    except KeyboardInterrupt:
        print("Translation process interrupted by user.")


if __name__ == "__main__":
    continuous_translation()
