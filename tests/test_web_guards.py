"""Request-level protections for the local web app.

The app must not run commands for hostile input, must not accept requests
that were forged by another website, and must not answer to foreign Host
headers (DNS rebinding).
"""

import subprocess

import pytest

import config
from web import app


@pytest.fixture
def client(monkeypatch):
    app.config.update(TESTING=True)
    spawned = []

    def fake_spawn(*args, **kwargs):
        spawned.append(args)
        raise AssertionError("a process must not be started for this request")

    monkeypatch.setattr(subprocess, "Popen", fake_spawn)
    monkeypatch.setattr(subprocess, "run", fake_spawn)
    monkeypatch.setattr("phone_scanner.privacy_scan_android.Popen", fake_spawn)

    c = app.test_client()
    c.spawned = spawned
    return c


def _login(client):
    with client.session_transaction() as s:
        s["clientid"] = 1


# --- injection through request parameters -------------------------------


def test_privacy_get_rejects_hostile_serial(client):
    r = client.get("/privacy/android/account/x/%3Becho%20PWNED")
    assert r.status_code == 400
    assert client.spawned == []


def test_privacy_get_rejects_hostile_serial_with_command_substitution(client):
    r = client.get("/privacy/android/screenshot/ctx/%24%28id%29")
    assert r.status_code == 400
    assert client.spawned == []


@pytest.mark.parametrize("context", ["..", "."])
def test_privacy_get_rejects_dot_segment_context(client, context):
    r = client.get(f"/privacy/android/screenshot/{context}/ZY224F8TKG")
    assert r.status_code == 400
    assert client.spawned == []


def test_privacy_get_rejects_dot_segment_serial(client):
    r = client.get("/privacy/android/screenshot/ctx/..")
    assert r.status_code == 400
    assert client.spawned == []


def test_scan_post_rejects_hostile_devid(client):
    _login(client)
    r = client.post(
        "/scan",
        data={"device": "android", "device_owner": "x", "devid": "x;echo PWNED"},
    )
    assert r.status_code == 400
    assert client.spawned == []


def test_delete_app_rejects_hostile_appid(client):
    r = client.post("/delete/app/1", data={"appid": "$(echo PWNED)", "remark": ""})
    assert r.status_code == 400
    assert client.spawned == []


# --- screenshot paths cannot leave the screenshots directory ---------------


def test_screenshot_path_stays_inside_screenshot_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "THIS_DIR", tmp_path)
    fname = config.create_screenshot_fname("Account 3", "ZY224F8TKG")
    root = (tmp_path / "webstatic" / "images" / "screenshots").resolve()
    assert str(fname).startswith(str(root))


@pytest.mark.parametrize(
    "context,serial",
    [("..", "x"), ("x", ".."), ("../../etc", "x"), ("x", "a/b"), ("", "x")],
)
def test_screenshot_path_rejects_traversal(tmp_path, monkeypatch, context, serial):
    monkeypatch.setattr(config, "THIS_DIR", tmp_path)
    with pytest.raises(ValueError):
        config.create_screenshot_fname(context, serial)


# --- cross-site and rebinding protection --------------------------------


def test_foreign_host_header_is_rejected(client):
    r = client.get("/privacy", headers={"Host": "evil.example:6200"})
    assert r.status_code == 403


@pytest.mark.parametrize("host", ["localhost:6200", "127.0.0.1:6200", "[::1]:6200"])
def test_local_host_headers_are_accepted(client, host):
    r = client.get("/privacy", headers={"Host": host})
    assert r.status_code == 200


def test_cross_site_get_cannot_delete_client_data(client, monkeypatch):
    deleted = []
    monkeypatch.setattr("web.view.evidence.delete_client_data", lambda: deleted.append(1))
    r = client.get("/evidence/delete-data", headers={"Sec-Fetch-Site": "cross-site"})
    assert r.status_code == 403
    assert deleted == []


def test_same_site_other_port_cannot_delete_client_data(client, monkeypatch):
    # Another local web app (for example localhost:3000) is "same-site" but
    # not same-origin, and must not be able to drive this app.
    deleted = []
    monkeypatch.setattr("web.view.evidence.delete_client_data", lambda: deleted.append(1))
    r = client.get("/evidence/delete-data", headers={"Sec-Fetch-Site": "same-site"})
    assert r.status_code == 403
    assert deleted == []


def test_same_origin_get_can_still_delete_client_data(client, monkeypatch):
    deleted = []
    monkeypatch.setattr("web.view.evidence.delete_client_data", lambda: deleted.append(1))
    r = client.get("/evidence/delete-data", headers={"Sec-Fetch-Site": "same-origin"})
    assert r.status_code in (302, 303)
    assert deleted == [1]


def test_request_without_fetch_metadata_still_works(client, monkeypatch):
    # Non-browser clients (curl, older browsers) send no Sec-Fetch-* headers.
    monkeypatch.setattr("web.view.evidence.delete_client_data", lambda: None)
    r = client.get("/evidence/delete-data")
    assert r.status_code in (302, 303)


@pytest.mark.parametrize("origin", ["http://evil.example", "null"])
def test_post_with_foreign_origin_is_rejected(client, origin):
    r = client.post("/scan", data={"device": "android"}, headers={"Origin": origin})
    assert r.status_code == 403


def test_post_with_local_origin_is_not_blocked_by_the_guard(client):
    # Without a session the route redirects to the index, which needs no database.
    r = client.post(
        "/scan",
        data={"device": "android"},
        headers={"Origin": "http://localhost:6200"},
    )
    assert r.status_code in (302, 303)
