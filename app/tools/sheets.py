"""Sheet CRM tools — plain args."""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.domain.shipment_row import ShipmentRow
from app.integrations.google import sheets as google_sheets
from app.services.fixture_store import get_fixture_store


def read_row_by_thread_id(thread_id: str) -> ShipmentRow | None:
    if settings.FIXTURE_MODE:
        store = get_fixture_store()
        for row in store.rows.values():
            if str(row.get("mail_thread_id") or "") == thread_id:
                return ShipmentRow.from_sheet_dict(row)
        return None
    return google_sheets.find_by_thread_id(thread_id)


def read_row_by_shipment_id(shipment_id: str) -> ShipmentRow | None:
    if settings.FIXTURE_MODE:
        raw = get_fixture_store().rows.get(shipment_id)
        return ShipmentRow.from_sheet_dict(raw) if raw else None
    return google_sheets.find_by_shipment_id(shipment_id)


def upsert_row(row: ShipmentRow) -> ShipmentRow:
    if settings.FIXTURE_MODE:
        get_fixture_store().rows[row.shipment_id] = row.to_sheet_dict()
        return row
    return google_sheets.upsert_row(row)


def patch_row(shipment_id: str, patch: dict[str, Any]) -> ShipmentRow:
    existing = read_row_by_shipment_id(shipment_id)
    if not existing:
        raise ValueError(f"shipment not found: {shipment_id}")
    data = existing.to_sheet_dict()
    data.update(patch)
    return upsert_row(ShipmentRow.from_sheet_dict(data))
