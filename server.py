import os
import random
from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import whisper
from datetime import datetime
from urllib.parse import urlencode
from llm_patient import generate_patient_utterance
import time

load_dotenv()
app = FastAPI()
model = whisper.load_model("tiny")

# Very simple state store
CALL_STATE = {}  # turn count
MAX_TURNS = 8
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
SCENARIOS = [
    "simple appointment scheduling as soon as possible, also medication refill request for a long list and your date of birth is 04/29/1999.",
    "reschedule an existing appointment do to emergency, your date of birth is 04/29/1999",
    "cancel appointment because of an insurance issue. Ask for department clarity.",
    "medication refill request for a long list, you are spanish speaking.",
    "Begin conversation by saying and spelling your full name (John Doe) and give phone number. ask about office hours and location. You are not in the system if asked.",
    "Ask if your insurance is in network (make up an insurance). Be a very talkative patient.",
    "Make an unclear request with jargon for the purpose of confusion",
    "Frustrated because of previous phone call (make up scenerio?)",
    "Be abrasive and rude regarding Pretty GoodAI service",
    "Schedule an appointment. You are unsure of what kind of appointment you need. Hesitate, ask vague questions, and change your mind once."
]

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

    # make sure to go second
    if call_sid not in CALL_STATE:
        CALL_STATE[call_sid] = {
            "turn": 0,
            "lines": [],
            "scenario": SCENARIOS[3], # Change to desired scenario
            "listened_greeting": False,
        }

    state = CALL_STATE[call_sid]

    recording_url = form.get("RecordingUrl")
    recording_sid = form.get("RecordingSid")
    # If we haven't listened to the opening greeting yet, do that first (no bot speech)
    if not state["listened_greeting"] and not recording_url:
        vr = VoiceResponse()
        vr.pause(length=1)  # optional but helps catch the greeting
        vr.record(
            max_length=12,
            play_beep=False,
            trim="trim-silence",
            action=f"{PUBLIC_BASE_URL}/voice",
            method="POST",
        )
        return Response(content=str(vr), media_type="application/xml")
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

        if not state["listened_greeting"]:
            state["listened_greeting"] = True

    if state["turn"] >= MAX_TURNS:
        state["lines"].append("BOT: Thanks for your help. Goodbye.")
        scenario = state.get("scenario", "unknown")

        if not state["lines"] or not state["lines"][0].startswith("SCENARIO:"):
            state["lines"].insert(0, f"SCENARIO: {scenario}")
        path = save_transcript(call_sid, state["lines"])
        print(f"[{call_sid}] Saved transcript: {path}")
        os.remove(wav_path)
        CALL_STATE.pop(call_sid, None)

        vr = VoiceResponse()
        vr.say("Thanks for your help. Goodbye.")
        vr.hangup()
        return Response(content=str(vr), media_type="application/xml")

    # need to change this to LLM call
    # bot_text = "Hi, I'm calling to schedule an appointment."
    scenario = state.get("scenario", "simple appointment scheduling")
    bot_text = generate_patient_utterance(state["lines"], scenario)
    state["lines"].append(f"BOT: {bot_text}")
    state["turn"] += 1
    CALL_STATE[call_sid] = state

    vr = VoiceResponse()
    vr.say(bot_text)

    vr.record(
        max_length=25,
        play_beep=False,
        trim="trim-silence",
        action=f"{PUBLIC_BASE_URL}/voice",
        method="POST",
    )

    return Response(content=str(vr), media_type="application/xml")

@app.post("/call_recording")
async def call_recording(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    recording_url = form.get("RecordingUrl")  # no extension

    if not recording_url:
        return Response("OK", media_type="text/plain")

    audio_url = recording_url + ".wav"
    r = requests.get(
        audio_url,
        auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        timeout=60,
    )
    r.raise_for_status()

    os.makedirs("full_calls", exist_ok=True)
    path = f"full_calls/{call_sid}.wav"
    with open(path, "wb") as f:
        f.write(r.content)

    print(f"[{call_sid}] Saved FULL call recording: {path}")
    return Response("OK", media_type="text/plain")

@app.post("/call_status")
async def call_status(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus")
    print(f"[{call_sid}] CallStatus: {call_status}")

    state = CALL_STATE.get(call_sid)
    if state and state.get("lines") and not state.get("saved"):
        scenario = state.get("scenario", "unknown")
        if not state["lines"][0].startswith("SCENARIO:"):
            state["lines"].insert(0, f"SCENARIO: {scenario}")
        path = save_transcript(call_sid, state["lines"])
        print(f"[{call_sid}] Saved transcript on status={call_status}: {path}")
        state["saved"] = True

    CALL_STATE.pop(call_sid, None)
    return Response("OK", media_type="text/plain")