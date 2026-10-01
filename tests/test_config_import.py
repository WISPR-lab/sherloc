"""Importing `config` must not create files or folders.

Scripts and tests import config just to read a setting; creating keys and
folders as a side effect of an import surprised them (CI created key files).
"""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SHERLOC = Path(__file__).resolve().parent.parent / "sherloc"


@pytest.fixture
def sandbox(tmp_path):
    """A copy of config.py in an empty directory, so its paths point there."""
    for name in ("config.py", "inputcheck.py"):
        shutil.copy(SHERLOC / name, tmp_path / name)
    (tmp_path / "static_data").mkdir()
    return tmp_path


def _run(sandbox, code):
    r = subprocess.run(
        [sys.executable, "-c", code],
        cwd=sandbox,
        env=dict(os.environ, PYTHONPATH=str(sandbox)),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def _tree(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if "__pycache__" not in str(p))


def test_importing_config_creates_nothing(sandbox):
    before = _tree(sandbox)
    _run(sandbox, "import config")
    assert _tree(sandbox) == before


def test_reading_a_key_creates_it_privately(sandbox):
    out = _run(
        sandbox,
        "import config; print(len(config.PII_KEY), len(config.FLASK_SECRET))",
    )
    assert out == "32 32"
    for name in ("pii.key", "flask.secret"):
        f = sandbox / "static_data" / name
        assert f.exists()
        if os.name == "posix":
            assert stat.S_IMODE(f.stat().st_mode) == 0o600


def test_a_key_is_stable_across_reads_and_processes(sandbox):
    a = _run(sandbox, "import config; print(config.PII_KEY.hex())")
    b = _run(sandbox, "import config; print(config.PII_KEY.hex()); import config as c; assert c.PII_KEY is config.PII_KEY")
    assert a == b


def test_hmac_serial_still_works(sandbox):
    out = _run(sandbox, "import config; print(config.hmac_serial('ABC'))")
    assert out.startswith("HSN_") and len(out) == 4 + 64


def test_ensure_dirs_creates_the_reports_folder(sandbox):
    assert not (sandbox / "reports").exists()
    _run(sandbox, "import config; config.ensure_dirs()")
    assert (sandbox / "reports").is_dir()
