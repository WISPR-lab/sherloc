"""Hostile device serials and app ids must never reach a shell.

Serials come from HTTP requests and from the connected device itself, and
app ids come from HTTP requests. Both end up in shell command lines.
"""

import subprocess

import pytest

from inputcheck import validate_appid, validate_serial
from phone_scanner import AndroidScan, IosScan

HOSTILE = [
    "",
    "x; echo PWNED",
    "$(echo PWNED)",
    "`echo PWNED`",
    "a b",
    "a|b",
    "a&b",
    "a'b",
    'a"b',
    "a\nb",
    "a\n",
    "..",
    ".",
    "x" * 300,
]

GOOD_SERIALS = [
    "ZY224F8TKG",
    "emulator-5554",
    "192.168.1.5:5555",
    "00008030-001234567890802E",
    "HSN_" + "a" * 64,
]

GOOD_APPIDS = [
    "com.example.app",
    "com.google.android.apps.pixelmigrate",
    "com.apple.mobilesafari",
    "org.my-app_2.beta",
]


@pytest.mark.parametrize("value", GOOD_SERIALS)
def test_validate_serial_accepts_real_serials(value):
    assert validate_serial(value) == value


@pytest.mark.parametrize("value", HOSTILE)
def test_validate_serial_rejects_hostile(value):
    with pytest.raises(ValueError):
        validate_serial(value)


@pytest.mark.parametrize("value", GOOD_APPIDS)
def test_validate_appid_accepts_real_ids(value):
    assert validate_appid(value) == value


@pytest.mark.parametrize("value", HOSTILE)
def test_validate_appid_rejects_hostile(value):
    with pytest.raises(ValueError):
        validate_appid(value)


@pytest.mark.parametrize("value", [None, 5, b"abc", ["a"]])
def test_validators_reject_non_strings(value):
    with pytest.raises(ValueError):
        validate_serial(value)
    with pytest.raises(ValueError):
        validate_appid(value)


class _Proc:
    """Stands in for subprocess.Popen: carries captured output only."""

    def __init__(self, out):
        self.out = out
        self.stdout = self
        self.returncode = 0

    def read(self):
        return self.out.encode()


@pytest.fixture
def shell(monkeypatch):
    """Run formatted commands in a real shell, with `adb` replaced by a
    function that prints each argument it receives. Nothing real is run.
    """
    runs = []

    def fake_run_command(cmd, **kwargs):
        kwargs.setdefault("cli", "adb")
        formatted = cmd.format(**kwargs)
        script = 'adb() { for a in "$@"; do printf "ARG:%s\\n" "$a"; done; }\n' + formatted
        out = subprocess.run(
            ["sh", "-c", script], capture_output=True, text=True, check=False
        ).stdout
        runs.append(out.split())
        return _Proc(out)

    monkeypatch.setattr("phone_scanner.run_command", fake_run_command)
    monkeypatch.setattr("phone_scanner.catch_err", lambda p, *a, **k: p.out)
    return runs


@pytest.mark.parametrize("appid", HOSTILE)
def test_android_uninstall_rejects_hostile_appid(shell, appid):
    with pytest.raises(ValueError):
        AndroidScan().uninstall(serial="ZY224F8TKG", appid=appid)
    assert shell == []


@pytest.mark.parametrize("appid", HOSTILE)
def test_ios_uninstall_rejects_hostile_appid(shell, appid):
    with pytest.raises(ValueError):
        IosScan().uninstall(serial="00008030-001234567890802E", appid=appid)
    assert shell == []


def test_android_uninstall_passes_appid_as_one_argument(shell):
    AndroidScan().uninstall(serial="ZY224F8TKG", appid="com.example.app")
    assert shell == [["ARG:uninstall", "ARG:com.example.app"]]


@pytest.mark.parametrize("serial", HOSTILE)
def test_android_device_info_rejects_hostile_serial(shell, serial):
    with pytest.raises(ValueError):
        AndroidScan().device_info(serial=serial)
    assert shell == []


@pytest.mark.parametrize("serial", HOSTILE)
def test_android_app_listing_rejects_hostile_serial(shell, serial):
    with pytest.raises(ValueError):
        AndroidScan()._get_apps_from_device(serial, "-u")
    assert shell == []


@pytest.mark.parametrize("serial", HOSTILE)
def test_android_rooted_check_rejects_hostile_serial(shell, serial):
    with pytest.raises(ValueError):
        AndroidScan().isrooted(serial)
    assert shell == []


def test_android_device_info_passes_serial_as_one_argument(shell):
    AndroidScan().device_info(serial="192.168.1.5:5555")
    first = shell[0]
    assert first[:3] == ["ARG:-s", "ARG:192.168.1.5:5555", "ARG:shell"]


@pytest.mark.parametrize("serial", HOSTILE)
def test_privacy_cli_rejects_hostile_serial(serial):
    from phone_scanner.privacy_scan_android import thiscli

    with pytest.raises(ValueError):
        thiscli(serial)


def test_privacy_cli_without_serial_targets_the_default_device():
    import config
    from phone_scanner.privacy_scan_android import thiscli

    assert thiscli(None) == config.ADB_PATH
