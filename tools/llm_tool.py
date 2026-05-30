"""
LLM helper — wraps OpenRouter's free-tier API.
Loads the .env from the project root regardless of which folder the script runs from.
"""

import os
import json
import requests
from pathlib import Path

# Find .env by walking up from this file's location
def _find_and_load_env():
    current = Path(__file__).resolve().parent
    for _ in range(4):  # walk up 4 levels max
        env_file = current / ".env"
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            return
        current = current.parent

_find_and_load_env()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

FREE_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-7b-instruct:free",
]


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    if not OPENROUTER_API_KEY:
        return "__LLM_UNAVAILABLE__"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://finance-agent.local",
        "X-Title":       "Finance Agent",
    }

    for model in FREE_MODELS:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        }
        try:
            resp = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            data = resp.json()
            if "error" in data:
                continue
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            continue

    return "__LLM_UNAVAILABLE__"
