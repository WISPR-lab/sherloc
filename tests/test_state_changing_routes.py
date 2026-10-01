"""Routes that delete data or stop the app must not be reachable with GET.

A GET can be triggered by an image tag, a link prefetch or a redirect. Only
POST is accepted, and no template links to these routes with an anchor.
"""

import re
from pathlib import Path

import pytest

import web  # noqa: F401  (import order: web first avoids a circular import)
from web import app

TEMPLATES = Path(__file__).resolve().parent.parent / "sherloc" / "templates"


@pytest.fixture(autouse=True)
def _no_real_side_effects(monkeypatch):
    # If a route regresses and a GET reaches its handler, it must not delete
    # real files or stop the test process.
    monkeypatch.setattr("web.view.evidence.delete_client_data", lambda: None)
    monkeypatch.setattr("web.view.evidence.load_object_from_json", lambda *_: [])
    monkeypatch.setattr("web.view.evidence.save_data_as_json", lambda *_: None)
    monkeypatch.setattr("web.view.control.stop_server", lambda: None)


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.mark.parametrize(
    "path",
    [
        "/evidence/delete-data",
        "/evidence/delete/account/0",
        "/evidence/delete/scan/ZY224F8TKG",
        "/kill",
        "/delete/app/1",
    ],
)
def test_get_is_not_allowed(client, path):
    assert client.get(path).status_code == 405


def test_delete_data_works_with_post(client, monkeypatch):
    deleted = []
    monkeypatch.setattr("web.view.evidence.delete_client_data", lambda: deleted.append(1))
    r = client.post("/evidence/delete-data")
    assert r.status_code in (302, 303)
    assert deleted == [1]


def test_cross_origin_post_cannot_delete_data(client, monkeypatch):
    deleted = []
    monkeypatch.setattr("web.view.evidence.delete_client_data", lambda: deleted.append(1))
    r = client.post("/evidence/delete-data", headers={"Origin": "http://evil.example"})
    assert r.status_code == 403
    assert deleted == []


def test_kill_with_post_stops_the_app(client, monkeypatch):
    stopped = []
    monkeypatch.setattr("web.view.control.stop_server", lambda: stopped.append(1))
    r = client.post("/kill")
    assert r.status_code == 200
    assert b"closed" in r.data
    assert stopped == [1]


def _template_text():
    for p in TEMPLATES.glob("*.html"):
        yield p.name, p.read_text()


def test_no_template_links_to_a_destructive_route_with_an_anchor():
    pattern = re.compile(
        r"<a\b[^>]*(url_for\(\s*['\"]evidence_delete_|href=[\"']/kill)", re.I
    )
    offenders = [name for name, text in _template_text() if pattern.search(text)]
    assert offenders == []


def test_app_ids_are_not_pasted_into_javascript_strings():
    # '{{ x }}' inside an onclick handler is HTML-escaped, then decoded by the
    # browser before the script runs, so a quote in the value breaks out.
    pattern = re.compile(r"delete_app\(\s*'\{\{")
    offenders = [name for name, text in _template_text() if pattern.search(text)]
    assert offenders == []
