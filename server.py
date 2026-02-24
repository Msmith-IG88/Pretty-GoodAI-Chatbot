import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import whisper

load_dotenv()
app = FastAPI()

# Very simple state store for now (good enough to start)
CALL_STATE = {}  # call_sid -> turn count, transcript, etc.
MAX_TURNS = 3
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")

    state = CALL_STATE.get(call_sid, {"turn": 0, "lines": []})
    turn = state["turn"]

    vr = VoiceResponse()

    if turn >= MAX_TURNS:
        vr.say("Thanks for your help. Goodbye.")
        vr.hangup()
        return Response(content=str(vr), media_type="application/xml")

    # otherwise continue conversation
    bot_text = "Hi, I'm calling to schedule an appointment."
    state["turn"] = turn + 1
    CALL_STATE[call_sid] = state

    vr.say(bot_text)
    vr.record(
        max_length=20,
        play_beep=False,
        recording_status_callback="/recording",
        recording_status_callback_method="POST",
        trim="trim-silence",
    )
    vr.redirect("/voice", method="POST")

    return Response(content=str(vr), media_type="application/xml")

@app.post("/recording")
async def recording(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    recording_url = form.get("RecordingUrl")  # no extension

    audio_url = recording_url + ".wav"

    response = requests.get(
        audio_url,
        auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    )

    os.makedirs("recordings", exist_ok=True)
    file_path = f"recordings/{call_sid}.wav"

    with open(file_path, "wb") as f:
        f.write(response.content)

    print(f"Saved recording to {file_path}")

    return Response(content="OK", media_type="text/plain")
