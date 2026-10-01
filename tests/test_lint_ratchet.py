"""Ratchet: the number of serious lint findings may go down, never up.

Existing findings are recorded per (file, rule) in lint_baseline.json. A new
finding fails this test; fixing one makes the test ask for the baseline to be
lowered, so the improvement is locked in.

Update the baseline after fixing findings with:

    python tests/test_lint_ratchet.py --update

Rules: F821 undefined name, W605 invalid escape sequence, B006 mutable default
argument, E722 bare except, S602 subprocess with shell=True, S307 eval.
"""

import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BASELINE = Path(__file__).with_name("lint_baseline.json")
RULES = "F821,W605,B006,E722,S602,S307"
TARGETS = ["sherloc", "tests"]


def current_findings():
    r = subprocess.run(
        [
            "ruff", "check", "--isolated", "--select", RULES,
            "--output-format", "json", "--no-cache", *TARGETS,
        ],
        cwd=ROOT, capture_output=True, text=True,
    )
    if r.returncode not in (0, 1):
        raise RuntimeError(f"ruff failed: {r.stderr}")
    counts = Counter()
    for item in json.loads(r.stdout or "[]"):
        rel = Path(item["filename"]).resolve().relative_to(ROOT).as_posix()
        counts[f"{rel}::{item['code']}"] += 1
    return dict(sorted(counts.items()))


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff is not installed")
def test_no_new_serious_lint_findings():
    baseline = json.loads(BASELINE.read_text())
    now = current_findings()

    worse = {k: (baseline.get(k, 0), n) for k, n in now.items() if n > baseline.get(k, 0)}
    assert not worse, (
        "New lint findings (baseline, now): "
        + json.dumps(worse, indent=2)
        + "\nFix them rather than raising the baseline."
    )

    better = {k: (n, now.get(k, 0)) for k, n in baseline.items() if now.get(k, 0) < n}
    assert not better, (
        "Findings were fixed. Lower the baseline with "
        "`python tests/test_lint_ratchet.py --update`: " + json.dumps(better, indent=2)
    )


if __name__ == "__main__":
    if "--update" in sys.argv:
        BASELINE.write_text(json.dumps(current_findings(), indent=2) + "\n")
        print(f"wrote {BASELINE}")
