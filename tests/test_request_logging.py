"""Request log lines must not contain device serials or other identifiers."""

import logging

import pytest

import web  # noqa: F401  (import order: web first avoids a circular import)
from web import app

SERIAL = "SECRETSERIAL1"


class _Scan:
    def app_details(self, serial, appid):
        return {"summary": "", "descriptionHTML": "", "permissions": []}, {}

    def uninstall(self, serial, appid):
        return True


@pytest.fixture
def client(monkeypatch):
    app.config.update(TESTING=True)
    monkeypatch.setattr("web.view.details.get_device", lambda d: _Scan())
    monkeypatch.setattr("web.view.evidence.load_object_from_json", lambda *_: [])
    monkeypatch.setattr("web.view.evidence.save_data_as_json", lambda *_: None)
    return app.test_client()


def _logged(caplog):
    return "\n".join(r.getMessage() for r in caplog.records)


def test_query_string_values_are_not_logged(client, caplog):
    with caplog.at_level(logging.DEBUG):
        client.get(f"/details/app/android?appId=com.example.app&serial={SERIAL}")
    assert SERIAL not in _logged(caplog)
    assert "com.example.app" not in _logged(caplog)


def test_path_parameters_are_not_logged(client, caplog):
    with caplog.at_level(logging.DEBUG):
        client.post(f"/evidence/delete/scan/{SERIAL}")
    assert SERIAL not in _logged(caplog)


def test_each_request_is_still_logged_with_method_route_and_status(client, caplog):
    with caplog.at_level(logging.DEBUG):
        client.post(f"/evidence/delete/scan/{SERIAL}")
    text = _logged(caplog)
    assert "POST" in text
    assert "/evidence/delete/scan/" in text  # the route pattern
    assert "302" in text


def test_unmatched_paths_are_logged_without_their_text(client, caplog):
    with caplog.at_level(logging.DEBUG):
        client.get(f"/no/such/page/{SERIAL}")
    text = _logged(caplog)
    assert SERIAL not in text
    assert "404" in text
