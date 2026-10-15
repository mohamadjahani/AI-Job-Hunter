import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load API key securely
env_path = Path(__file__).parent / "secrets" / ".env"
load_dotenv(env_path)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found")

client = OpenAI(api_key=api_key)

print("Connecting to OpenAI...")

response = client.responses.create(
    model="gpt-5.4-mini",
    input=(
        "You are an IT career advisor. "
        "Give one short English sentence explaining "
        "why Windows troubleshooting is useful "
        "for an IT Support Technician."
    ),
    max_output_tokens=150,
)

print("\nAI RESPONSE:")
print(response.output_text)
