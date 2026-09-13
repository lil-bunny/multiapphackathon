"""OpenAI chat_json helper for classification and extraction."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.core.config import settings


class LLMError(Exception):
    pass


def chat_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        raise LLMError("OPENAI_API_KEY required")
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM returned non-JSON: {content[:200]}") from exc
