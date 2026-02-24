import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
public_base_url = os.getenv("PUBLIC_BASE_URL")  # your ngrok https URL

client = Client(account_sid, auth_token)

call = client.calls.create(
    to="+18054398008",
    from_=twilio_number,
    url=f"{public_base_url}/voice",
    method="POST"
)

print("Call SID:", call.sid)