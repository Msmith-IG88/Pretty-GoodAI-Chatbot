import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import whisper
from datetime import datetime
from urllib.parse import urlencode

load_dotenv()
app = FastAPI()
model = whisper.load_model("base")

# Very simple state store
CALL_STATE = {}  # turn count
MAX_TURNS = 3
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")

def transcribe_audio(path) -> str:
    result = model.transcribe(path)
    return (result.get("text") or "").strip()

def save_transcript(call_sid: str, lines: list[str]) -> str:
    os.makedirs("calls", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = f"calls/{ts}_{call_sid}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return out_path

@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")

    state = CALL_STATE.get(call_sid, {"turn": 0, "lines": []})

    recording_url = form.get("RecordingUrl")
    recording_sid = form.get("RecordingSid")
    if recording_url:

        audio_url = recording_url + ".wav"
        r = requests.get(audio_url, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=30)
        r.raise_for_status()

        os.makedirs("recordings", exist_ok=True)
        wav_path = f"recordings/{call_sid}_{recording_sid}.wav"
        with open(wav_path, "wb") as f:
            f.write(r.content)

        text = transcribe_audio(wav_path)
        state["lines"].append(f"AGENT: {text}")
        print(f"[{call_sid}] AGENT SAID: {text}")

    if state["turn"] >= MAX_TURNS:
        state["lines"].append("BOT: Thanks for your help. Goodbye.")
        path = save_transcript(call_sid, state["lines"])
        print(f"[{call_sid}] Saved transcript: {path}")
        CALL_STATE.pop(call_sid, None)

        vr = VoiceResponse()
        vr.say("Thanks for your help. Goodbye.")
        vr.hangup()
        return Response(content=str(vr), media_type="application/xml")

    # need to change this to LLM call
    bot_text = "Hi, I'm calling to schedule an appointment."
    state["lines"].append(f"BOT: {bot_text}")
    state["turn"] += 1
    CALL_STATE[call_sid] = state

    vr = VoiceResponse()
    vr.say(bot_text)

    # Key part: action posts back to /voice after recording completes
    vr.record(
        max_length=20,
        play_beep=False,
        trim="trim-silence",
        action=f"{PUBLIC_BASE_URL}/voice",
        method="POST",
    )

    return Response(content=str(vr), media_type="application/xml")

@app.post("/recording")
async def recording(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    recording_url = form.get("RecordingUrl")  # no extension
    recording_sid = form.get("RecordingSid")

    # ignore after convo has ended
    if call_sid not in CALL_STATE:
        return Response(content="OK", media_type="text/plain")

    audio_url = recording_url + ".wav"

    response = requests.get(
        audio_url,
        auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        timeout=30,
    )
    response.raise_for_status()

    os.makedirs("recordings", exist_ok=True)
    file_path = f"recordings/{call_sid}_{recording_sid}.wav"

    with open(file_path, "wb") as f:
        f.write(response.content)

    print(f"Saved recording to {file_path}")
    text = transcribe_audio(file_path)
    print(f"[{call_sid}] AGENT SAID: {text}")

    state = CALL_STATE.get(call_sid, {"turn": 0, "lines": []})
    state["lines"].append(f"AGENT: {text}")
    CALL_STATE[call_sid] = state

    return Response(content="OK", media_type="text/plain")
