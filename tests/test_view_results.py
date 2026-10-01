"""/view_results is a work-in-progress route. It must not crash."""

import pytest

import web  # noqa: F401  (import order: web first avoids a circular import)
from web import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_view_results_with_an_existing_scan_redirects(client, monkeypatch):
    row = {"serial": "ZY224F8TKG", "device": "android", "device_model": "Pixel"}
    monkeypatch.setattr("web.view.results.get_scan_res_from_db", lambda pk: [row])
    r = client.get("/view_results?scan_res=1")
    assert r.status_code in (302, 303)


def test_view_results_without_a_scan_says_so(client, monkeypatch):
    monkeypatch.setattr("web.view.results.get_scan_res_from_db", lambda pk: [])
    r = client.get("/view_results?scan_res=999")
    assert r.status_code == 200
    assert b"No scan found" in r.data
