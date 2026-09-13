"""Thin Unipile HTTP client for hackathon mail I/O."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class UnipileError(Exception):
    pass


class UnipileClient:
    def __init__(self) -> None:
        api_key = settings.UNIPILE_API_KEY
        if not api_key:
            raise UnipileError("UNIPILE_API_KEY not set")
        dsn = (settings.UNIPILE_DSN or "api11.unipile.com:14157").strip("\"'")
        self.base_url = f"https://{dsn}/api/v1"
        self.client = httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0))

    def _headers(self) -> dict[str, str]:
        return {"X-API-KEY": settings.UNIPILE_API_KEY, "Accept": "application/json"}

    def get_email(self, email_id: str, *, account_id: str | None = None) -> dict[str, Any]:
        params: dict[str, str] = {}
        if account_id:
            params["account_id"] = account_id
        resp = self.client.get(
            f"{self.base_url}/emails/{email_id}",
            headers=self._headers(),
            params=params,
        )
        if resp.status_code != 200:
            raise UnipileError(f"get_email failed: {resp.text}")
        return resp.json()

    def list_emails(
        self,
        *,
        account_id: str,
        thread_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, str | int] = {"account_id": account_id, "limit": limit}
        if thread_id:
            params["thread_id"] = thread_id
        resp = self.client.get(
            f"{self.base_url}/emails",
            headers=self._headers(),
            params=params,
        )
        if resp.status_code != 200:
            raise UnipileError(f"list_emails failed: {resp.text}")
        data = resp.json()
        if isinstance(data, dict):
            items = data.get("items") or data.get("emails") or []
            return items if isinstance(items, list) else []
        return data if isinstance(data, list) else []

    def get_email_attachment(
        self,
        email_id: str,
        attachment_id: str,
        *,
        account_id: str | None = None,
    ) -> bytes:
        params: dict[str, str] = {}
        if account_id:
            params["account_id"] = account_id
        resp = self.client.get(
            f"{self.base_url}/emails/{email_id}/attachments/{attachment_id}",
            headers=self._headers(),
            params=params,
        )
        if resp.status_code != 200:
            raise UnipileError(f"get_attachment failed: {resp.text}")
        return resp.content

    def send_email(
        self,
        *,
        account_id: str,
        to: list[dict[str, str]],
        subject: str,
        body: str,
        reply_to: str | None = None,
        cc: list[dict[str, str]] | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "account_id": account_id,
            "subject": subject,
            "body": body,
            "to": json.dumps(to),
        }
        if reply_to:
            data["reply_to"] = reply_to
        if cc:
            data["cc"] = json.dumps(cc)
        files = []
        for name, content, mime in attachments or []:
            files.append(("attachments", (name, content, mime)))
        headers = self._headers()
        if files:
            resp = self.client.post(
                f"{self.base_url}/emails",
                headers=headers,
                data=data,
                files=files,
            )
        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            resp = self.client.post(
                f"{self.base_url}/emails",
                headers=headers,
                data=data,
            )
        if resp.status_code not in (200, 201):
            return {"success": False, "error": resp.text}
        result = resp.json()
        return {"success": True, "tracking_id": result.get("tracking_id"), "response": result}
