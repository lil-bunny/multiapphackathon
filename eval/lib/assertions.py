"""Shared eval assertions for isolated cases and multi-step scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.fixture_store import FixtureStore

CRM_FIELDS = (
    "shipment_id",
    "delivery_date",
    "driver_name",
    "driver_phone",
    "driver_email",
    "current_delivery_datetime",
    "delay_reason",
    "status",
    "mail_thread_id",
    "customer_email",
    "customer_notice_version",
)


@dataclass
class SideEffectSnapshot:
    email_counts: dict[str, int]
    slack_count: int


def snapshot_store(store: FixtureStore) -> SideEffectSnapshot:
    counts: dict[str, int] = {}
    for email in store.sent_emails:
        key = str(email.get("email_type") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return SideEffectSnapshot(email_counts=counts, slack_count=len(store.slack_alerts))


def _crm_from_data(data: dict[str, Any], store: FixtureStore) -> dict[str, Any]:
    crm = data.get("crm_row")
    if isinstance(crm, dict) and crm.get("shipment_id"):
        return crm
    shipment_id = str(data.get("shipment_id") or "")
    if shipment_id and shipment_id in store.rows:
        return dict(store.rows[shipment_id])
    return crm if isinstance(crm, dict) else {}


def _assert_crm(crm: dict[str, Any], expected: dict[str, Any]) -> str | None:
    for key, want in expected.items():
        got = crm.get(key)
        if key == "customer_notice_version":
            if int(got or 0) != int(want):
                return f"crm.{key} expected {want!r} got {got!r}"
        elif got != want:
            return f"crm.{key} expected {want!r} got {got!r}"
    return None


def _assert_state(data: dict[str, Any], expected: dict[str, Any]) -> str | None:
    for key, want in expected.items():
        if data.get(key) != want:
            return f"state.{key} expected {want!r} got {data.get(key)!r}"
    return None


def _assert_email_delta(
    before: SideEffectSnapshot,
    after: SideEffectSnapshot,
    expected: dict[str, int],
) -> str | None:
    for email_type, want_delta in expected.items():
        got_delta = after.email_counts.get(email_type, 0) - before.email_counts.get(
            email_type, 0
        )
        if got_delta != want_delta:
            return (
                f"emails_delta.{email_type} expected +{want_delta} got +{got_delta} "
                f"(total {after.email_counts.get(email_type, 0)})"
            )
    return None


def _assert_email_totals(store: FixtureStore, expected: dict[str, int]) -> str | None:
    snap = snapshot_store(store)
    for email_type, want in expected.items():
        got = snap.email_counts.get(email_type, 0)
        if got != want:
            return f"emails.{email_type} expected {want} got {got}"
    return None


def assert_step(
    *,
    data: dict[str, Any],
    store: FixtureStore,
    expect: dict[str, Any],
    before: SideEffectSnapshot | None = None,
) -> tuple[bool, str]:
    """Return (ok, message). Supports nested scenario expects and legacy flat cases."""
    if expect.get("no_errors"):
        for key in (
            "workflow_error",
            "carrier_ack_error",
            "delivery_followup_error",
            "on_track_ack_error",
        ):
            if data.get(key):
                return False, f"unexpected {key}={data.get(key)!r}"

    crm = _crm_from_data(data, store)

    if "crm" in expect:
        err = _assert_crm(crm, expect["crm"])
        if err:
            return False, err

    if "state" in expect:
        err = _assert_state(data, expect["state"])
        if err:
            return False, err

    after = snapshot_store(store)
    if "emails_delta" in expect:
        if before is None:
            return False, "emails_delta requires a before snapshot"
        err = _assert_email_delta(before, after, expect["emails_delta"])
        if err:
            return False, err

    if "slack_delta" in expect:
        if before is None:
            return False, "slack_delta requires a before snapshot"
        want = int(expect["slack_delta"])
        got = after.slack_count - before.slack_count
        if got != want:
            return False, f"slack_delta expected +{want} got +{got}"

    if "emails_total" in expect:
        err = _assert_email_totals(store, expect["emails_total"])
        if err:
            return False, err

    if "slack_total" in expect:
        want = int(expect["slack_total"])
        if after.slack_count != want:
            return False, f"slack_total expected {want} got {after.slack_count}"

    # Legacy flat CRM + side-effect keys (isolated eval cases)
    if "crm" not in expect:
        legacy_crm = {
            k: expect[k] for k in CRM_FIELDS if k in expect
        }
        if legacy_crm:
            err = _assert_crm(crm, legacy_crm)
            if err:
                return False, err

        if "customer_emails_sent" in expect:
            err = _assert_email_totals(store, {"customer": expect["customer_emails_sent"]})
            if err:
                return False, err.replace("emails.customer", "customer_emails_sent")

        if "carrier_ack_emails_sent" in expect:
            err = _assert_email_totals(
                store, {"carrier_ack": expect["carrier_ack_emails_sent"]}
            )
            if err:
                return False, err.replace("emails.carrier_ack", "carrier_ack_emails_sent")

        if "slack_alerts_sent" in expect:
            if after.slack_count != expect["slack_alerts_sent"]:
                return False, (
                    f"slack_alerts_sent expected {expect['slack_alerts_sent']} "
                    f"got {after.slack_count}"
                )

    return True, "ok"
