from pathlib import Path

from eval.lib.assertions import assert_step, snapshot_store
from eval.run_demo import run_scenario


def test_run_scenario_reports_clear_failure_on_bad_expect() -> None:
    root = Path(__file__).resolve().parents[1]
    scenario_path = root / "eval" / "scenarios" / "happy_path.json"

    import json

    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    scenario["steps"][-1]["expect"]["crm"]["status"] = "definitely_wrong"

    bad_path = root / "eval" / "scenarios" / "_test_bad_expect.json"
    bad_path.write_text(json.dumps(scenario), encoding="utf-8")
    try:
        passed, total, lines = run_scenario(bad_path, verbose=False)
        assert passed < total
        assert any("FAIL" in line for line in lines)
    finally:
        bad_path.unlink(missing_ok=True)


def test_assert_step_emails_delta_requires_before_snapshot() -> None:
    from app.services.fixture_store import FixtureStore

    store = FixtureStore()
    ok, msg = assert_step(
        data={},
        store=store,
        expect={"emails_delta": {"customer": 1}},
        before=None,
    )
    assert ok is False
    assert "before snapshot" in msg


def test_assert_step_emails_delta_counts_new_messages() -> None:
    from app.services.fixture_store import FixtureStore

    store = FixtureStore()
    before = snapshot_store(store)
    store.sent_emails.append({"email_type": "customer", "to": "a@b.com"})
    ok, msg = assert_step(
        data={},
        store=store,
        expect={"emails_delta": {"customer": 1}},
        before=before,
    )
    assert ok is True, msg
