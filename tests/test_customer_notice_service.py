from unittest.mock import patch

from app.domain.shipment_row import ShipmentRow
from app.services.customer_notice_service import CustomerNoticeService


def test_publish_update_emails_customer_and_patches_sheet():
    row = ShipmentRow(
        shipment_id="SHP-2099",
        customer_email="customer@example.com",
        delivery_date="2026-09-15",
        current_delivery_datetime="2026-09-16 14:00",
        delay_reason="Weather",
        customer_notice_version=0,
    )
    patched = row.model_copy(update={"customer_notice_version": 1})

    emailed = patched.model_copy(
        update={"last_customer_emailed_at": "2026-09-14 00:00:00 UTC"}
    )

    with (
        patch(
            "app.services.customer_notice_service.mail_tools.send_customer_email",
            return_value={"success": True},
        ) as send_mail,
        patch(
            "app.services.customer_notice_service.sheet_tools.patch_row",
            return_value=emailed,
        ) as patch_row,
    ):
        result = CustomerNoticeService().publish_update(row)

    send_mail.assert_called_once()
    patch_row.assert_called_once()
    row_patch = patch_row.call_args[0][1]
    assert row_patch["customer_notice_version"] == 1
    assert "last_customer_emailed_at" in row_patch
    assert result.customer_notice_version == 1
