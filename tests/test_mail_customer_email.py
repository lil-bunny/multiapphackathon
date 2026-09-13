from app.tools.mail import send_customer_email


def test_send_customer_email_strips_whitespace(monkeypatch):
    captured: dict = {}

    class FakeClient:
        def send_email(self, **kwargs):
            captured.update(kwargs)
            return {"success": True}

    monkeypatch.setattr(
        "app.tools.mail.settings.FIXTURE_MODE",
        False,
    )
    monkeypatch.setattr(
        "app.tools.mail.settings.UNIPILE_API_KEY",
        "test-key",
    )
    monkeypatch.setattr(
        "app.tools.mail.settings.UNIPILE_ACCOUNT_ID",
        "acct-1",
    )
    monkeypatch.setattr("app.tools.mail.UnipileClient", lambda: FakeClient())

    result = send_customer_email(
        to_email="customer@example.com ",
        subject="Update",
        body="Hello",
    )

    assert result["success"] is True
    assert captured["to"][0]["identifier"] == "customer@example.com"
