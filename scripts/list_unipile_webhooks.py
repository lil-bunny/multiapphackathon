"""List Unipile webhooks (format, URL, id)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

key = os.environ.get("UNIPILE_API_KEY", "")
dsn = (os.environ.get("UNIPILE_DSN") or "").strip("\"'")
if not key or not dsn:
    print("Set UNIPILE_API_KEY and UNIPILE_DSN in .env", file=sys.stderr)
    raise SystemExit(1)

resp = httpx.get(
    f"https://{dsn}/api/v1/webhooks",
    headers={"X-API-KEY": key, "Accept": "application/json"},
    timeout=15.0,
)
resp.raise_for_status()
items = resp.json().get("items", [])
for webhook in items:
    print(
        json.dumps(
            {
                "id": webhook.get("id"),
                "name": webhook.get("name"),
                "format": webhook.get("format"),
                "request_url": webhook.get("request_url"),
                "source": webhook.get("source"),
                "events": webhook.get("events"),
            },
            indent=2,
        )
    )
