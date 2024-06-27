import asyncio
from io import BytesIO

import websockets
from gtts import gTTS
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionTextToSpeech(Action):

    def name(self) -> str:
        return "action_text_to_speech"

    async def send_audio(self, websocket_uri, text):
        async with websockets.connect(websocket_uri) as websocket:
            tts = gTTS(text=text, lang='en')
            audio_fp = BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            await websocket.send(audio_fp.read())

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        response_text = tracker.latest_message.get('text')
        websocket_uri = "ws://localhost:8000/audio"
        asyncio.run(self.send_audio(websocket_uri, response_text))
        
        dispatcher.utter_message(text="Audio response is being sent...")
        return []
