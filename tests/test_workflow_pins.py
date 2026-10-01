"""Every GitHub Action is pinned to a full commit hash.

A tag such as @v4 can be moved to different code after it was reviewed.
"""

import re
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)", re.M)
PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")


def test_every_action_is_pinned_to_a_commit_hash():
    unpinned = []
    for wf in sorted(WORKFLOWS.glob("*.y*ml")):
        for ref in USES.findall(wf.read_text()):
            if ref.startswith("./"):
                continue
            if not PINNED.match(ref):
                unpinned.append(f"{wf.name}: {ref}")
    assert unpinned == []


def test_there_are_workflows_to_check():
    assert list(WORKFLOWS.glob("*.y*ml"))
