"""Start-up behaviour: the `test` argument and a missing blocklist."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

SHERLOC = Path(__file__).resolve().parent.parent / "sherloc"


@pytest.mark.parametrize("arg", ["test", "TEST"])
def test_test_argument_turns_on_test_mode(arg):
    from runmode import apply_cli_mode

    env = {}
    assert apply_cli_mode(["main.py", arg], env) is True
    assert env["TEST"] == "1"


def test_no_argument_leaves_the_environment_alone():
    from runmode import apply_cli_mode

    env = {}
    assert apply_cli_mode(["main.py"], env) is False
    assert env == {}


def test_main_applies_the_argument_before_config_is_imported():
    text = (SHERLOC / "main.py").read_text()
    assert "apply_cli_mode" in text
    assert text.index("apply_cli_mode(") < text.index("import config")


def test_missing_blocklist_exits_with_an_error():
    code = (
        "import config; config.APP_FLAGS_FILE = 'static_data/does-not-exist.csv'; "
        "import phone_scanner.blocklist"
    )
    env = dict(os.environ, PYTHONPATH=f"{SHERLOC}:{SHERLOC / 'phone_scanner'}")
    r = subprocess.run(
        [sys.executable, "-c", code], cwd=SHERLOC, env=env, capture_output=True, text=True
    )
    assert r.returncode != 0
    assert "blocklist" in (r.stdout + r.stderr).lower()
