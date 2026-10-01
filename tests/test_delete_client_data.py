"""Deleting client data must remove it from the database, not only from disk."""

import sqlite3
from pathlib import Path

import pytest

import web  # noqa: F401  (import order: web first avoids a circular import)
import config
import evidence_collection as ec

SCHEMA = Path(config.THIS_DIR) / "web" / "schema.sql"
MARKERS = [b"MARKER-NOTE-7731", b"MARKER-SERIAL-7731", b"MARKER-REMARK-7731"]


@pytest.fixture
def populated(tmp_path, monkeypatch):
    dbfile = tmp_path / "fieldstudy.db"
    con = sqlite3.connect(dbfile)
    con.executescript(SCHEMA.read_text())
    con.execute(
        "insert into clients_notes (clientid, general_notes) values (?, ?)",
        ("20260101_001", MARKERS[0].decode()),
    )
    con.execute(
        "insert into scan_res (clientid, serial) values (?, ?)",
        ("20260101_001", MARKERS[1].decode()),
    )
    con.execute(
        "insert into app_info (scanid, appid, remark) values (1, 'a.b', ?)",
        (MARKERS[2].decode(),),
    )
    con.commit()
    con.close()

    # point everything the deletion touches at temporary locations
    for name in ("DUMP_DIR", "SCREENSHOT_DIR", "REPORT_DIR"):
        d = tmp_path / name
        d.mkdir()
        (d / "client-file.txt").write_text("x")
        monkeypatch.setattr(ec, name, d)
    monkeypatch.setattr(ec, "TMP_CONSULT_DATA_DIR", str(tmp_path / "consult"))
    monkeypatch.setattr(config, "SQL_DB_PATH", f"sqlite:///{dbfile}")
    return dbfile


def _rows(dbfile, table):
    con = sqlite3.connect(dbfile)
    try:
        return con.execute(f"select count(*) from {table}").fetchone()[0]
    finally:
        con.close()


def test_rows_are_removed_from_every_client_table(populated):
    ec.delete_client_data()
    for table in ("clients_notes", "scan_res", "app_info"):
        assert _rows(populated, table) == 0, table


def test_deleted_text_is_not_left_in_the_database_file(populated):
    ec.delete_client_data()
    raw = populated.read_bytes()
    for marker in MARKERS:
        assert marker not in raw


def test_schema_is_kept_so_the_app_still_works(populated):
    ec.delete_client_data()
    con = sqlite3.connect(populated)
    try:
        con.execute(
            "insert into clients_notes (clientid, general_notes) values ('c', 'n')"
        )
        names = {
            r[0]
            for r in con.execute("select name from sqlite_master where type='table'")
        }
    finally:
        con.close()
    assert {"clients_notes", "scan_res", "app_info"} <= names


def test_files_are_still_deleted(populated):
    ec.delete_client_data()
    assert list(Path(ec.DUMP_DIR).iterdir()) == []
    assert list(Path(ec.SCREENSHOT_DIR).iterdir()) == []
    assert list(Path(ec.REPORT_DIR).iterdir()) == []


def test_missing_database_is_not_an_error(tmp_path, monkeypatch):
    for name in ("DUMP_DIR", "SCREENSHOT_DIR", "REPORT_DIR"):
        d = tmp_path / name
        d.mkdir()
        monkeypatch.setattr(ec, name, d)
    monkeypatch.setattr(ec, "TMP_CONSULT_DATA_DIR", str(tmp_path / "consult"))
    monkeypatch.setattr(config, "SQL_DB_PATH", f"sqlite:///{tmp_path / 'none.db'}")
    ec.delete_client_data()
    assert not (tmp_path / "none.db").exists()


def test_sql_statements_are_not_echoed_to_logs():
    # Echoed statements include client notes and device serials.
    assert web.app.config["SQLALCHEMY_ECHO"] is False


def test_database_is_wiped_even_if_a_folder_is_missing(populated, tmp_path, monkeypatch):
    # A crash while removing files must not leave the database untouched.
    monkeypatch.setattr(ec, "DUMP_DIR", tmp_path / "never-created")
    monkeypatch.setattr(ec, "REPORT_DIR", tmp_path / "also-missing")
    ec.delete_client_data()
    assert _rows(populated, "clients_notes") == 0
    assert (tmp_path / "never-created").is_dir()  # recreated, as for the others
