"""Run golden eval cases against fixture-mode workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.domain.state import WorkflowState
from app.services.fixture_store import get_fixture_store
from app.workflows.graph import get_compiled_graph
from eval.lib.assertions import assert_step

settings.FIXTURE_MODE = True


def _load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_case(case_path: Path) -> tuple[bool, str]:
    case = _load_json(case_path)
    store = get_fixture_store()
    store.reset()

    if case.get("initial_rows"):
        rows_path = ROOT / case["initial_rows"]
        store.load_rows(_load_json(rows_path))

    graph = get_compiled_graph()
    state = WorkflowState(data=case["payload"])
    result = graph.invoke(state)
    data = result.data if isinstance(result, WorkflowState) else result.get("data", result)
    return assert_step(data=data, store=store, expect=case["expect"])


def main() -> int:
    cases_dir = Path(__file__).parent / "cases"
    case_files = sorted(cases_dir.glob("*.json"))
    passed = 0
    for case_file in case_files:
        ok, msg = _run_case(case_file)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {case_file.name}: {msg}")
        if ok:
            passed += 1
    print(f"\n{passed}/{len(case_files)} passed")
    return 0 if passed == len(case_files) else 1


if __name__ == "__main__":
    raise SystemExit(main())
