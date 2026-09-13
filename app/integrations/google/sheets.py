"""Google Sheets CRM read/write via service account."""

from __future__ import annotations

from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import settings
from app.domain.shipment_row import SHEET_COLUMNS, ShipmentRow

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_RANGE = "Sheet1!A:N"


class GoogleSheetsError(Exception):
    pass


def _service():
    if not settings.GOOGLE_SERVICE_ACCOUNT_JSON:
        raise GoogleSheetsError("GOOGLE_SERVICE_ACCOUNT_JSON not configured")
    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_JSON,
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _sheet_id() -> str:
    sid = str(settings.GOOGLE_SHEET_ID or "").strip()
    if not sid:
        raise GoogleSheetsError("GOOGLE_SHEET_ID not configured")
    return sid


def read_all_rows() -> list[ShipmentRow]:
    result = _service().spreadsheets().values().get(
        spreadsheetId=_sheet_id(),
        range=SHEET_RANGE,
    ).execute()
    values = result.get("values") or []
    if not values:
        return []
    header = [str(h).strip() for h in values[0]]
    rows: list[ShipmentRow] = []
    for raw in values[1:]:
        row_dict = {header[i]: raw[i] if i < len(raw) else "" for i in range(len(header))}
        if str(row_dict.get("shipment_id") or "").strip():
            rows.append(ShipmentRow.from_sheet_dict(row_dict))
    return rows


def _row_to_values(row: ShipmentRow) -> list[str | int]:
    data = row.to_sheet_dict()
    return [data.get(col, "") for col in SHEET_COLUMNS]


def _ensure_header() -> None:
    svc = _service()
    sid = _sheet_id()
    existing = svc.spreadsheets().values().get(spreadsheetId=sid, range="Sheet1!A1:N1").execute()
    if not existing.get("values"):
        svc.spreadsheets().values().update(
            spreadsheetId=sid,
            range="Sheet1!A1:N1",
            valueInputOption="RAW",
            body={"values": [SHEET_COLUMNS]},
        ).execute()


def upsert_row(row: ShipmentRow) -> ShipmentRow:
    _ensure_header()
    rows = read_all_rows()
    sid = _sheet_id()
    svc = _service()
    values = _row_to_values(row)

    for idx, existing in enumerate(rows, start=2):
        if existing.shipment_id == row.shipment_id:
            svc.spreadsheets().values().update(
                spreadsheetId=sid,
                range=f"Sheet1!A{idx}:N{idx}",
                valueInputOption="RAW",
                body={"values": [values]},
            ).execute()
            return row

    svc.spreadsheets().values().append(
        spreadsheetId=sid,
        range=SHEET_RANGE,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [values]},
    ).execute()
    return row


def find_by_thread_id(thread_id: str) -> ShipmentRow | None:
    tid = str(thread_id or "").strip()
    if not tid:
        return None
    for row in read_all_rows():
        if row.mail_thread_id == tid:
            return row
    return None


def find_by_shipment_id(shipment_id: str) -> ShipmentRow | None:
    sid = str(shipment_id or "").strip()
    if not sid:
        return None
    for row in read_all_rows():
        if row.shipment_id == sid:
            return row
    return None
