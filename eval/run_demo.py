"""Single-run hackathon demo eval — full workflow scenarios in fixture mode."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.domain.state import WorkflowState
from app.services.fixture_store import get_fixture_store
from app.workflows.graph import get_compiled_graph
from eval.lib.assertions import assert_step, snapshot_store

settings.FIXTURE_MODE = True

FOLLOWUP_WAIT_PADDING_S = 0.3


def _load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def _apply_scenario_settings(scenario: dict) -> None:
    for key, value in (scenario.get("settings") or {}).items():
        if hasattr(settings, key):
            setattr(settings, key, value)


def _format_step_line(index: int, total: int, label: str, ok: bool) -> str:
    dots = "." * max(1, 42 - len(label))
    status = "OK" if ok else "FAIL"
    return f"  [{index}/{total}] {label} {dots} {status}"


def run_scenario(scenario_path: Path, *, verbose: bool = True) -> tuple[int, int, list[str]]:
    scenario = _load_json(scenario_path)
    store = get_fixture_store()
    store.reset()
    _apply_scenario_settings(scenario)

    if scenario.get("initial_rows"):
        rows_path = ROOT / scenario["initial_rows"]
        store.load_rows(_load_json(rows_path))

    graph = get_compiled_graph()
    steps = scenario.get("steps") or []
    passed = 0
    lines: list[str] = []

    if verbose:
        print(f"\nScenario: {scenario.get('name', scenario_path.stem)}")

    for idx, step in enumerate(steps, start=1):
        label = str(step.get("label") or f"step {idx}")
        step_type = str(step.get("type") or "invoke")
        before = snapshot_store(store)
        data: dict = {}

        if step_type == "assert_store":
            data = {"crm_row": dict(store.rows.get("SHP-2099") or {})}
            if not data["crm_row"]:
                for row in store.rows.values():
                    data["crm_row"] = dict(row)
                    break
        elif step_type == "wait_followup":
            delay = max(0, int(settings.DELIVERY_FOLLOWUP_DELAY_SECONDS))
            time.sleep(delay + FOLLOWUP_WAIT_PADDING_S)
            shipment_id = str(step.get("shipment_id") or "")
            if not shipment_id:
                for row in store.rows.values():
                    shipment_id = str(row.get("shipment_id") or "")
                    if shipment_id:
                        break
            if shipment_id and shipment_id in store.rows:
                data = {"crm_row": dict(store.rows[shipment_id])}
        else:
            payload = step.get("payload") or {}
            result = graph.invoke(WorkflowState(data=payload))
            data = result.data if isinstance(result, WorkflowState) else result.get("data", result)

        ok, msg = assert_step(
            data=data,
            store=store,
            expect=step.get("expect") or {},
            before=before,
        )
        line = _format_step_line(idx, len(steps), label, ok)
        lines.append(line)
        if verbose:
            print(line)
            if not ok:
                print(f"         -> {msg}")

        if ok:
            passed += 1
        else:
            return passed, len(steps), lines

    return passed, len(steps), lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run hackathon E2E demo eval scenarios")
    parser.add_argument(
        "--scenario",
        action="append",
        help="Scenario file name under eval/scenarios/ (default: all)",
    )
    args = parser.parse_args(argv)

    scenarios_dir = Path(__file__).parent / "scenarios"
    if args.scenario:
        scenario_files = [scenarios_dir / name for name in args.scenario]
    else:
        scenario_files = sorted(
            scenarios_dir.glob("*.json"),
            key=lambda p: (p.stem != "happy_path", p.name),
        )

    print("=== Shipment Agent — Demo Eval (fixture mode) ===")

    total_passed = 0
    total_steps = 0
    for scenario_path in scenario_files:
        if not scenario_path.exists():
            print(f"\nMissing scenario: {scenario_path}")
            return 1
        passed, steps, _lines = run_scenario(scenario_path)
        total_passed += passed
        total_steps += steps
        if passed < steps:
            print(
                f"\nFAILED ({total_passed}/{total_steps} steps) — "
                f"fix scenario {scenario_path.name} before demo"
            )
            return 1

    print(f"\nALL PASSED ({total_passed}/{total_steps} steps) — workflow ready for demo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
