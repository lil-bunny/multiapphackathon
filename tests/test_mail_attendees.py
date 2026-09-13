from app.domain.mail_attendees import reply_all_cc, reply_all_cc_from_emails


def test_reply_all_cc_keeps_other_recipients() -> None:
    email = {
        "to_attendees": [
            {"identifier": "asleepf011@gmail.com", "display_name": "Ops"},
            {"identifier": "getrichfunway@gmail.com", "display_name": "Broker"},
        ],
        "cc_attendees": [],
        "from_attendee": {"identifier": "carrier@example.com"},
    }
    cc = reply_all_cc(
        email,
        primary_to="carrier@example.com",
        exclude_emails={"asleepf011@gmail.com"},
    )
    assert len(cc) == 1
    assert cc[0]["identifier"] == "getrichfunway@gmail.com"


def test_reply_all_cc_from_emails_merges_ratecon_and_reply() -> None:
    ratecon = {
        "from_attendee": {"identifier": "debdutrcks@gmail.com", "display_name": "Debdut"},
        "to_attendees": [
            {"identifier": "getrichfunway@gmail.com", "display_name": "Broker"},
            {"identifier": "chakrabortyshatavisha2@gmail.com", "display_name": "Shatavisha"},
            {"identifier": "asleepf011@gmail.com", "display_name": "Ops"},
        ],
        "cc_attendees": [],
    }
    driver_reply = {
        "from_attendee": {"identifier": "chakrabortyshatavisha2@gmail.com"},
        "to_attendees": [
            {"identifier": "debdutrucks@gmail.com"},
            {"identifier": "getrichfunway@gmail.com"},
            {"identifier": "asleepf011@gmail.com"},
        ],
        "cc_attendees": [],
    }
    cc = reply_all_cc_from_emails(
        [ratecon, driver_reply],
        primary_to="debdutrcks@gmail.com",
        exclude_emails={"asleepf011@gmail.com"},
    )
    identifiers = {item["identifier"] for item in cc}
    assert identifiers == {
        "debdutrucks@gmail.com",
        "getrichfunway@gmail.com",
        "chakrabortyshatavisha2@gmail.com",
    }


def test_reply_all_cc_from_emails_dedupes_across_messages() -> None:
    emails = [
        {
            "to_attendees": [{"identifier": "broker@example.com"}],
            "cc_attendees": [],
        },
        {
            "to_attendees": [{"identifier": "broker@example.com"}],
            "cc_attendees": [{"identifier": "customer@example.com"}],
        },
    ]
    cc = reply_all_cc_from_emails(
        emails,
        primary_to="carrier@example.com",
        exclude_emails=set(),
    )
    assert len(cc) == 2
    assert {c["identifier"] for c in cc} == {"broker@example.com", "customer@example.com"}
