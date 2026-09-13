from __future__ import annotations

DRIVER_DETAILS = "driver_details"
DELIVERY_DELAY = "delivery_delay"
DELIVERY_STATUS = "delivery_status"
INSUFFICIENT = "insufficient"
DO_NOTHING = "do_nothing"

VALID_INTENTS = frozenset(
    {DRIVER_DETAILS, DELIVERY_DELAY, DELIVERY_STATUS, INSUFFICIENT, DO_NOTHING}
)
