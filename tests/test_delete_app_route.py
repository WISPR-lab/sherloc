"""delete_app must uninstall from the device that was scanned."""

import pytest

import config
import web  # noqa: F401  (import order: web first avoids a circular import)
from web import app

REAL = "ZY224F8TKG"


class _Scan:
    def __init__(self):
        self.calls = []

    def uninstall(self, serial, appid):
        self.calls.append((serial, appid))
        return True


@pytest.fixture
def setup(monkeypatch):
    app.config.update(TESTING=True)
    scan = _Scan()
    monkeypatch.setattr("web.view.save.get_device", lambda d: scan)
    monkeypatch.setattr("web.view.save.get_device_from_db", lambda scanid: "android")
    # The database stores the pseudonymized serial, never the real one.
    monkeypatch.setattr(
        "web.view.save.get_serial_from_db", lambda scanid: config.hmac_serial(REAL)
    )
    monkeypatch.setattr("web.view.save.update_appinfo", lambda **kw: 1)
    return app.test_client(), scan


def test_uninstalls_from_the_posted_device_when_it_matches_the_scan(setup):
    client, scan = setup
    r = client.post("/delete/app/1", data={"appid": "com.example.app", "serial": REAL})
    assert r.status_code == 200
    assert scan.calls == [(REAL, "com.example.app")]


def test_refuses_a_serial_that_is_not_the_scanned_device(setup):
    client, scan = setup
    r = client.post(
        "/delete/app/1", data={"appid": "com.example.app", "serial": "OTHERDEVICE1"}
    )
    assert r.status_code == 400
    assert scan.calls == []


def test_refuses_a_missing_serial(setup):
    client, scan = setup
    r = client.post("/delete/app/1", data={"appid": "com.example.app"})
    assert r.status_code == 400
    assert scan.calls == []


def test_refuses_a_hostile_serial(setup):
    client, scan = setup
    r = client.post(
        "/delete/app/1", data={"appid": "com.example.app", "serial": "x;echo PWNED"}
    )
    assert r.status_code == 400
    assert scan.calls == []
