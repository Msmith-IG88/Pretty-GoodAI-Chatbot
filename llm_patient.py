import os
from openai import OpenAI

SYSTEM = """You are a realistic patient calling a medical office AI assistant..."""

def generate_patient_utterance(history_lines: list[str], scenario: str) -> str:
    # Create client 
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    history = "\n".join(history_lines[-20:])
    user = f"""Scenario: {scenario}

Conversation so far:
{history}

Return ONLY the next thing the patient should say (no quotes, no labels)."""

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()