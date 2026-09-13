"""Slack incoming-webhook alerts."""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.services.fixture_store import get_fixture_store

logger = get_logger(__name__)


def send_webhook_alert(text: str) -> bool:
    if settings.FIXTURE_MODE:
        get_fixture_store().slack_alerts.append({"text": text})
        return True

    url = str(settings.SLACK_WEBHOOK_URL or "").strip()
    if not url:
        logger.warning("slack webhook not configured; alert skipped")
        return False

    response = httpx.post(url, json={"text": text}, timeout=10.0)
    response.raise_for_status()
    return True
