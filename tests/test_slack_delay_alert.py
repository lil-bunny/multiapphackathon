from unittest.mock import patch

from app.domain.shipment_row import ShipmentRow
from app.domain.state import WorkflowState
from app.workflows.nodes.crm import apply_crm_update


def test_apply_crm_update_sends_slack_on_delay():
    state = WorkflowState(
        data={
            "reply_intent": "delivery_delay",
            "thread_id": "thread-1042",
            "classification": {
                "delay": {
                    "new_delivery_datetime": "2026-09-16 14:00",
                    "reason": "Rain",
                }
            },
        }
    )
    updated = ShipmentRow(
        shipment_id="SHP-1042",
        current_delivery_datetime="2026-09-16 14:00",
        delay_reason="Rain",
        status="delayed",
    )

    with (
        patch(
            "app.workflows.nodes.crm.ShipmentCrmService.match_row",
            return_value=updated,
        ),
        patch(
            "app.workflows.nodes.crm.ShipmentCrmService.apply_reply_update",
            return_value=(updated, True, False, False),
        ),
        patch(
            "app.workflows.nodes.crm.SlackAlertService.send_delay_alert",
        ) as send_alert,
    ):
        result = apply_crm_update(state)

    send_alert.assert_called_once_with(updated)
    assert result.data["should_notify_customer"] is True
