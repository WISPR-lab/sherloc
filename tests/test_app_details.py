"""/details/app renders text from Play Store and App Store crawls, which anyone can write."""

import pytest

import web  # noqa: F401  (import order: web first avoids a circular import)
from web import app

HOSTILE_DESCRIPTION = (
    "<b>Tracks</b> you<script>alert(1)</script>"
    '<img src=x onerror="alert(2)">'
    '<a href="javascript:alert(3)" onclick="alert(4)">click</a>'
    "<iframe src=\"file:///etc/passwd\"></iframe>"
)


class _Scan:
    def app_details(self, serial, appid):
        d = {
            "summary": HOSTILE_DESCRIPTION,
            "descriptionHTML": HOSTILE_DESCRIPTION,
            "title": "T",
            "permissions": [],
        }
        return d, {}


@pytest.fixture
def client(monkeypatch):
    app.config.update(TESTING=True)
    monkeypatch.setattr("web.view.details.get_device", lambda device: _Scan())
    return app.test_client()


def test_hostile_description_is_neutralised(client):
    r = client.get("/details/app/android?appId=com.example.app&serial=ZY224F8TKG")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    # the page itself has script tags, so look for the hostile markers only
    for bad in ("alert(1)", "alert(2)", "alert(3)", "alert(4)", "<img src=x",
                "javascript:alert", "file:///etc/passwd", "<iframe"):
        assert bad not in body, bad


def test_harmless_formatting_is_kept(client):
    r = client.get("/details/app/android?appId=com.example.app&serial=ZY224F8TKG")
    assert "<b>Tracks</b>" in r.get_data(as_text=True)


@pytest.mark.parametrize(
    "query",
    [
        "appId=%24%28id%29&serial=ZY224F8TKG",
        "appId=com.example.app&serial=..%2F..%2Fetc",
        "appId=com.example.app&serial=a%3Bb",
        "appId=&serial=ZY224F8TKG",
    ],
)
def test_hostile_identifiers_are_rejected(client, monkeypatch, query):
    called = []
    monkeypatch.setattr(
        "web.view.details.get_device", lambda device: called.append(1) or _Scan()
    )
    r = client.get(f"/details/app/android?{query}")
    assert r.status_code == 400
    assert called == []


def test_unknown_device_is_rejected(client, monkeypatch):
    monkeypatch.setattr("web.view.details.get_device", lambda device: None)
    r = client.get("/details/app/mainframe?appId=a.b&serial=ZY224F8TKG")
    assert r.status_code in (400, 404)
