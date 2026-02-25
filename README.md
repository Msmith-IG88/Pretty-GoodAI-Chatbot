# Pretty-GoodAI-Chatbot

A FastAPI-based Twilio Voice bot that uses Whisper for transcription and a lightweight LLM helper to generate patient utterances. The application exposes a small set of endpoints to handle live calls, recordings, and call status.

This project simulates a patient calling a medical office using a Twilio Voice workflow.  
It:

- Receives live call audio via Twilio
- Transcribes speech using Whisper
- Generates patient responses using an LLM
- Logs transcripts and full-call recordings
- Supports multiple testing scenarios for evaluation

This was built to evaluate conversational behavior and identify agent-side bugs through structured call simulations.

## Prerequisites

- Python 3.8+ (tested with 3.10)
- Git (optional, for cloning)
- Twilio account with Voice capability and a configured phone number
- Awareness of public URL exposure for local development (see Ngrok below)
- Basic command line knowledge (Windows / macOS / Linux)

## Project at a glance

- Entry point: `server.py`
- Web API: FastAPI app with endpoints:
  - POST `/voice` – handles live voice call interactions and bot responses
  - POST `/call_recording` – stores full call recordings
  - POST `/call_status` – saves transcripts on call status changes
- Local transcription: Whisper model (tiny)
- Speech-to-text is handled locally using OpenAI's Whisper model (requires PyTorch)

## Environment configuration

Create a local environment file (recommended) named `.env` with the following variables:

```
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
PUBLIC_BASE_URL=http://localhost:8000           # Will be overwritten by ngrok when testing publicly
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

Notes:
- PUBLIC_BASE_URL must be reachable by Twilio. When running locally, you can expose your machine with ngrok or similar and update PUBLIC_BASE_URL accordingly.
- The app uses dotenv to load these values.

If you have a pre-existing environment setup (e.g., a `requirements.txt` or a virtual environment), adapt commands accordingly.

## Setup and installation

1) Create and activate a virtual environment

- Windows (PowerShell)
  - Python 3.x must be in PATH
  - python -m venv .venv
  - .\.venv\Scripts\activate

- macOS/Linux
  - python3 -m venv .venv
  - source .venv/bin/activate

2) Install dependencies

- use:
  - pip install -r requirements.txt

- Otherwise, install core dependencies directly:
  - pip install fastapi uvicorn python-dotenv requests twilio whisper
  - Note: Whisper relies on PyTorch. Follow Whisper installation guidance for your platform if you encounter issues:
    - Typical starting point: pip install torch torchvision torchaudio
    - Or follow the official Whisper installation instructions (e.g., installing from GitHub).

3) Prepare environment variables
- Create a `.env` file (or ensure existing `.env` is properly configured as shown above).

4) Verify Python can import modules
- Run a quick import test:
  - python -c "import fastapi, whisper, dotenv"

## Run the application

- If you are testing locally and need public access:
  - Install and run ngrok (https://ngrok.com)
  - Expose port 8000:
    - ngrok http 8000
  - Copy the generated public URL (e.g., https://abcd1234.ngrok.io) and set PUBLIC_BASE_URL in your `.env` to that URL.

- Twilio webhook setup
  - Point your Twilio phone number’s Voice webhook to:
    - POST {PUBLIC_BASE_URL}/voice
  - Ensure your Twilio account has valid credentials (SID and Auth Token) placed in the environment.

- Start the FastAPI server (host accessible from local network or publicly exposed)
  - Command:
    - python run.py

## How to test

- You can initiate a test by simulating a call through Twilio’s testing tools or by wiring up a real Twilio number to the webhook. The server handles:
  - Greeting (with a recording prompt)
  - Transcribing the caller’s audio via Whisper
  - Generating a bot utterance via the `generate_patient_utterance` function from `llm_patient.py`
  - Saving transcripts to `calls/` and full recordings to `full_calls/`

- Local script test
  - python test_call.py

The bot supports configurable scenarios defined in `server.py`. The scenario is stored in call state and logged at the top of each transcript. 

## Endpoints overview

- POST /voice
  - Handles the voice flow: greeting, transcription, and bot prompts
- POST /call_recording
  - Saves a full call recording to `full_calls/`
- POST /call_status
  - Saves transcripts when the call ends or reaches a terminal status

## File/directory overview

- run.py: Setup using simple uvicorn and ngrok commands
- server.py: Main FastAPI app and route handlers
- llm_patient.py: Generates patient utterances (LLM-backed logic)
- test_call.py: Basic test or demonstration script
- calls/: Transcript storage for individual calls
- full_calls/: Full-length call recordings
- recordings/: (placeholder for downloaded audio or interim storage)

## Troubleshooting

- Environment variables missing
  - Ensure `.env` exists and contains TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and PUBLIC_BASE_URL
- Twilio webhook not reachable
  - Use ngrok or deploy to a publicly accessible server. Update PUBLIC_BASE_URL accordingly
- Whisper model not loading or slow
  - Confirm PyTorch and Whisper installation, and that the environment has sufficient resources
- Port conflicts
  - If 8000 is in use, choose another port and update PUBLIC_BASE_URL accordingly

## Licensing and contributions

- This project is intended for experimentation and prototyping. Please add your own LICENSE if you plan to publicize.
- For contributions, fork the repository and submit PRs with clear, tested changes.