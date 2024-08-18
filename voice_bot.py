import os
from io import BytesIO

import requests
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play

# Specify the path to ffmpeg and ffprobe executables
ffmpeg_path = "C:\\Users\\hello\\Downloads\\ffmpeg-master-latest-win64-gpl\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe"
ffprobe_path = "C:\\Users\\hello\\Downloads\\ffmpeg-master-latest-win64-gpl\\ffmpeg-master-latest-win64-gpl\\bin\\ffprobe.exe"

# Set the PATH environment variable in the script
os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_path)

# Check if the ffmpeg and ffprobe paths are correct
if not os.path.isfile(ffmpeg_path):
    raise FileNotFoundError(f"ffmpeg executable not found at {ffmpeg_path}")

if not os.path.isfile(ffprobe_path):
    raise FileNotFoundError(f"ffprobe executable not found at {ffprobe_path}")

AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Adjusting for ambient noise, please wait...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Please say something...")
        audio = recognizer.listen(source)
        print("Audio captured, processing...")

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return None
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return None

def get_rasa_response(text):
    url = "http://localhost:5005/webhooks/rest/webhook"
    payload = {"message": text}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()[0]['text']
    except requests.RequestException as e:
        print(f"Error during request: {e}")
        return "Sorry, I couldn't get a response from the bot."

def speak_text(text, speed=1.0):
    tts = gTTS(text=text, lang='en')
    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    audio = AudioSegment.from_file(audio_fp, format="mp3")

    # Adjust the playback speed
    if speed != 1.0:
        audio = audio.speedup(playback_speed=speed)

    play(audio)