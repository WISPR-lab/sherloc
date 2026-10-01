"""iOS screenshots: arguments are passed as a list, and the tunnel is always stopped."""

import importlib
import subprocess

import pytest

import web  # noqa: F401  (import order: web first avoids a circular import)

# web.view re-exports a function named `privacy`, so import the module by name
privacy = importlib.import_module("web.view.privacy")

TUNNEL_OUTPUT = [
    b"Identifier: abc\n",
    b"Interface: utun5\n",
    b"Protocol: TunnelProtocol.QUIC\n",
    b"RSD Address: fd12:3456::1\n",
    b"RSD Port: 49152\n",
    b"Use the follow connection option:\n",
    b"--rsd fd12:3456::1 49152\n",
]


class FakeTunnel:
    def __init__(self, lines=TUNNEL_OUTPUT):
        self.stdout = iter(lines)
        self.terminated = False
        self.waited = False

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        self.waited = True

    def kill(self):
        self.terminated = True


@pytest.fixture
def env(monkeypatch, tmp_path):
    state = {"tunnel": FakeTunnel(), "runs": []}
    fname = str(tmp_path / "My Installs" / "shot.png")
    monkeypatch.setattr(privacy.config, "create_screenshot_fname", lambda c, s: fname)
    monkeypatch.setattr(privacy.time, "sleep", lambda s: None)
    monkeypatch.setattr(
        privacy.subprocess, "Popen", lambda *a, **k: state["tunnel"]
    )

    def fake_run(argv, **kwargs):
        state["runs"].append(argv)
        if state.get("fail"):
            raise subprocess.CalledProcessError(3, argv)

    monkeypatch.setattr(privacy.subprocess, "run", fake_run)
    state["fname"] = fname
    return state


def _call():
    from web import app

    with app.test_request_context("/"):
        return privacy.iosScreenshot("00008030-001234567890802E", "ctx", nocache=True)


def test_command_is_a_list_and_keeps_a_path_with_spaces_whole(env):
    _call()
    argv = env["runs"][0]
    assert isinstance(argv, list)
    assert env["fname"] in argv
    assert argv[argv.index("--rsd") + 1 : argv.index("--rsd") + 3] == ["fd12:3456::1", "49152"]


def test_rsd_values_have_no_trailing_newline(env):
    _call()
    assert not any("\n" in a for a in env["runs"][0])


def test_tunnel_is_stopped_after_success(env):
    _call()
    assert env["tunnel"].terminated


def test_tunnel_is_stopped_after_failure(env):
    env["fail"] = True
    out = _call()
    assert "screenshotfail" in out
    assert env["tunnel"].terminated


def test_tunnel_is_stopped_when_no_rsd_info_appears(env):
    env["tunnel"] = FakeTunnel(lines=[b"nothing useful\n"])
    out = _call()
    assert "screenshotfail" in out
    assert env["tunnel"].terminated
    assert env["runs"] == []
