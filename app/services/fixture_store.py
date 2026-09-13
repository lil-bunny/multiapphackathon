"""In-memory CRM, Slack, and mail side-effects for fixture/eval mode."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FixtureStore:
    rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    slack_alerts: list[dict[str, Any]] = field(default_factory=list)
    sent_emails: list[dict[str, Any]] = field(default_factory=list)

    def reset(self) -> None:
        self.rows.clear()
        self.slack_alerts.clear()
        self.sent_emails.clear()

    def load_rows(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            sid = str(row.get("shipment_id") or "").strip()
            if sid:
                self.rows[sid] = dict(row)


# Module singleton for eval runs
_store = FixtureStore()


def get_fixture_store() -> FixtureStore:
    return _store
