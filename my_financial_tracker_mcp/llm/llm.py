import os
from dotenv import load_dotenv
from google import genai
import re
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def llm_call(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    return response.text


def parse_llm_json(text: str):
    if not text or not text.strip():
        raise ValueError("Empty LLM response")

    # rimuove markdown
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    # estrae JSON
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in:\n{text}")

    return json.loads(match.group(0))