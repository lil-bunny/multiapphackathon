"""LLM classification for email thread replies."""

from __future__ import annotations

from typing import Any

from app.tools.llm import LLMError, chat_json
from app.tools.reply_parse import build_reply_classification_result

REPLY_CLASSIFY_PROMPT = """Classify a freight email thread reply.
Return JSON:
{
  "intent": "driver_details" | "delivery_delay" | "delivery_status" | "insufficient" | "do_nothing",
  "confidence": float,
  "reason": str,
  "driver": {"name": str|null, "phone": str|null, "email": str|null},
  "delay": {"new_delivery_datetime": str|null, "delay_hours": str|null, "reason": str|null}
}
Use delivery_delay when the reply mentions ETA change, hours late, weather, rain, etc.
Use delivery_status when the reply confirms on-time / in transit / approaching delivery with no delay."""


class ReplyClassificationService:
    def classify(
        self,
        thread_text: str,
        *,
        fixture_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if fixture_result:
            return build_reply_classification_result(fixture_result)
        try:
            raw = chat_json(REPLY_CLASSIFY_PROMPT, thread_text)
        except LLMError:
            raw = {"intent": "do_nothing", "confidence": 0.0, "reason": "llm unavailable"}
        return build_reply_classification_result(raw)
