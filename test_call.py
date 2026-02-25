import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
public_base_url = os.getenv("PUBLIC_BASE_URL") 

client = Client(account_sid, auth_token)

call = client.calls.create(
    to="+18054398008",
    from_=twilio_number,
    url=f"{public_base_url}/voice",
    method="POST",
    record=True,
    recording_status_callback=f"{public_base_url}/call_recording",
    recording_status_callback_method="POST",
    status_callback=f"{public_base_url}/call_status",
    status_callback_method="POST",
    status_callback_event=["completed", "busy", "failed", "no-answer"],
)

print("Call SID:", call.sid)