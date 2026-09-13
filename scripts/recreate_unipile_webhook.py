"""Delete + recreate Unipile email webhook with format=json."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

WEBHOOK_PATH = "/webhook/unipile"


def _client() -> tuple[str, dict[str, str]]:
    key = os.environ.get("UNIPILE_API_KEY", "")
    dsn = (os.environ.get("UNIPILE_DSN") or "").strip("\"'")
    if not key or not dsn:
        print("Set UNIPILE_API_KEY and UNIPILE_DSN in .env", file=sys.stderr)
        raise SystemExit(1)
    return f"https://{dsn}/api/v1", {"X-API-KEY": key, "Accept": "application/json"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="hackathon")
    parser.add_argument(
        "--url",
        default="",
        help="Full webhook URL (default: https://$NGROK_DOMAIN/webhook/unipile)",
    )
    parser.add_argument(
        "--account-id",
        default=os.environ.get("UNIPILE_ACCOUNT_ID", ""),
        help="Unipile account id (default: UNIPILE_ACCOUNT_ID from .env)",
    )
    args = parser.parse_args()

    url = args.url.strip()
    if not url:
        domain = (os.environ.get("NGROK_DOMAIN") or "").strip().removeprefix("https://").removeprefix("http://")
        if not domain:
            print("Pass --url or set NGROK_DOMAIN in .env", file=sys.stderr)
            return 1
        url = f"https://{domain.rstrip('/')}{WEBHOOK_PATH}"

    account_id = args.account_id.strip()
    if not account_id:
        print("Pass --account-id or set UNIPILE_ACCOUNT_ID in .env", file=sys.stderr)
        return 1

    base, headers = _client()
    with httpx.Client(timeout=30.0) as client:
        items = client.get(f"{base}/webhooks", headers=headers).json().get("items", [])
        for webhook in items:
            if webhook.get("name") == args.name:
                wid = webhook["id"]
                client.delete(f"{base}/webhooks/{wid}", headers=headers).raise_for_status()
                print(f"Deleted webhook {args.name!r} id={wid}")

        body = {
            "source": "email",
            "request_url": url,
            "name": args.name,
            "format": "json",
            "events": ["mail_received"],
            "enabled": True,
            "account_ids": [account_id],
        }
        secret = (os.environ.get("UNIPILE_WEBHOOK_SECRET") or "").strip()
        if secret:
            body["headers"] = [{"key": "x-webhook-secret", "value": secret}]

        created = client.post(f"{base}/webhooks", headers=headers, json=body)
        created.raise_for_status()
        print(f"Created {args.name!r} -> {url} format=json")
        print(json.dumps(created.json(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
