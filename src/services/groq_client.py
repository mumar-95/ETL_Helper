"""Thin Groq client with JSON extraction."""

from __future__ import annotations

import json
import re
from typing import Any

from src.config import get_settings


def get_client():
    from groq import Groq

    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured. Set it in .env or .streamlit/secrets.toml")
    return Groq(api_key=settings.groq_api_key)


def chat_completion(messages: list[dict[str, str]], *, temperature: float = 0.3) -> str:
    settings = get_settings()
    client = get_client()
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def extract_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))
