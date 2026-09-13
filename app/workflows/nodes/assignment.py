from __future__ import annotations

from pathlib import Path

from app.core.logger import get_logger
from app.domain.state import WorkflowState
from app.services.shipment_crm_service import ShipmentCrmService
from app.tools import mail as mail_tools
from app.tools import pdf_extract

logger = get_logger(__name__)


def process_assignment_pdf(state: WorkflowState) -> WorkflowState:
    data = state.data
    pdf_bytes: bytes | None = data.get("pdf_bytes")
    if not pdf_bytes and data.get("pdf_bytes_path"):
        pdf_bytes = Path(str(data["pdf_bytes_path"])).read_bytes()
    if not pdf_bytes and data.get("fixture_pdf_bytes") is not None:
        raw = data["fixture_pdf_bytes"]
        pdf_bytes = raw if isinstance(raw, bytes) else str(raw).encode()
    if not pdf_bytes and data.get("email_id") and data.get("attachment_id"):
        pdf_bytes = mail_tools.fetch_pdf_attachment_bytes(
            email_id=str(data["email_id"]),
            attachment_id=str(data["attachment_id"]),
            account_id=data.get("account_id"),
        )
    if not pdf_bytes:
        state.data["workflow_error"] = "missing_pdf_bytes"
        return state

    extracted = pdf_extract.extract_assignment_from_pdf(
        pdf_bytes,
        fixture_result=data.get("fixture_pdf_extract"),
    )
    shipment_id = pdf_extract.shipment_id_from_attachment_name(
        str(data.get("attachment_name") or "")
    ) or str(extracted.get("shipment_id") or "").strip()
    delivery_date = str(extracted.get("delivery_date") or "").strip()
    if not shipment_id:
        state.data["workflow_error"] = "pdf_extract_incomplete"
        return state

    crm = ShipmentCrmService()
    existing = crm.match_row(shipment_id=shipment_id)
    if not delivery_date and existing:
        delivery_date = existing.delivery_date
    if not delivery_date:
        state.data["workflow_error"] = "pdf_extract_incomplete"
        return state

    row = crm.upsert_assignment(
        shipment_id=shipment_id,
        delivery_date=delivery_date,
        mail_thread_id=str(data.get("thread_id") or ""),
        customer_email=str(data.get("customer_email") or ""),
    )
    state.data["shipment_id"] = row.shipment_id
    state.data["crm_row"] = row.to_sheet_dict()
    logger.info("assignment processed shipment_id=%s", shipment_id)
    return state
