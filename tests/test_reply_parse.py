from app.domain.reply_intent import DELIVERY_DELAY, DRIVER_DETAILS, INSUFFICIENT
from app.tools.reply_parse import build_reply_classification_result, validate_driver_fields


def test_driver_details_requires_name_and_contact() -> None:
    assert validate_driver_fields({"name": "John", "phone": None, "email": None}) == INSUFFICIENT
    assert validate_driver_fields({"name": "John", "phone": "555", "email": None}) == DRIVER_DETAILS


def test_delay_classification_requires_reason() -> None:
    result = build_reply_classification_result(
        {
            "intent": "delivery_delay",
            "delay": {"delay_hours": "3", "reason": "Rain"},
            "driver": {},
        }
    )
    assert result["intent"] == DELIVERY_DELAY


def test_unknown_intent_becomes_do_nothing() -> None:
    result = build_reply_classification_result({"intent": "maybe", "driver": {}, "delay": {}})
    assert result["intent"] == "do_nothing"
