"""The PDF printout is rendered from user-entered text by wkhtmltopdf.

Notes, nicknames and app names are free text, and wkhtmltopdf can read local
files, so that text must be escaped before it is turned into HTML.
"""

import re
import shutil
import subprocess

import pytest

import web  # noqa: F401  (import order: web first avoids a circular import)
import evidence_collection as ec

SECTIONS = ("devices", "accounts", "sharing", "smarthome", "kids")

PAYLOADS = [
    '<iframe src="file:///etc/passwd"></iframe>',
    "<img src=x onerror=alert(1)>",
    "<script>document.write('x')</script>",
]


def _context(**overrides):
    ctx = {
        "url_root": "http://localhost:6200/",
        "sherloc_version": "test",
        "setup": {"client": "Client", "date": "2026-01-01"},
        "notes": {"consultant_notes": "", "client_notes": ""},
        "scans": [],
        "accounts": [],
        "taq": {
            "all_risks": [],
            **{k: {"risk_report": {"risk_details": []}} for k in SECTIONS},
        },
        "formquestions": {"taq": {"devices": {}, "accounts": {}, "sharing": {}, "smarthome": {}, "kids": {}}},
        "select_text": {},
        "risks": [],
    }
    ctx.update(overrides)
    return ctx


@pytest.mark.parametrize("payload", PAYLOADS)
def test_notes_are_escaped_in_the_printout_html(payload):
    ctx = _context(notes={"consultant_notes": payload, "client_notes": payload})
    html = ec.render_printout_html(ctx)
    assert payload not in html
    assert "<iframe" not in html
    assert "<script>" not in html
    assert "<img src=x" not in html


def test_client_name_is_escaped_in_the_printout_html():
    payload = PAYLOADS[0]
    ctx = _context(setup={"client": payload, "date": "now"})
    assert payload not in ec.render_printout_html(ctx)


def test_ordinary_text_is_kept():
    ctx = _context(notes={"consultant_notes": "Tom & Jerry's phone", "client_notes": ""})
    html = ec.render_printout_html(ctx)
    assert "Tom &amp; Jerry&#39;s phone" in html


def test_pdf_options_do_not_enable_local_file_access():
    opts = ec.printout_pdf_options()
    assert not opts.get("enable-local-file-access")


@pytest.mark.skipif(shutil.which("wkhtmltopdf") is None, reason="wkhtmltopdf not installed")
def test_a_hostile_note_does_not_pull_a_local_file_into_the_pdf(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP-SECRET-MARKER-12345")
    ctx = _context(
        notes={
            "consultant_notes": f'<iframe src="file://{secret}" width="500" height="200"></iframe>',
            "client_notes": "",
        }
    )
    out = ec.create_printout(ctx, out_file=str(tmp_path / "out.pdf"))
    text = subprocess.run(
        ["pdftotext", out, "-"], capture_output=True, text=True
    ).stdout if shutil.which("pdftotext") else ""
    assert "TOP-SECRET-MARKER-12345" not in text
    assert re.search(rb"%PDF", open(out, "rb").read(8))
