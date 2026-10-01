"""`evidence_collection` is imported by name from many places.

The module was split into smaller ones; every public name it offered must
still be importable from it, with the same kind of object. Names that
are only imported libraries (wtforms fields, `re`, `Path`...) are not part
of the API and are not listed.
"""

import inspect
from pathlib import Path

import pytest

import web  # noqa: F401  (import order: web first avoids a circular import)
import evidence_collection as ec

SNAPSHOT = Path(__file__).with_name("evidence_collection_api.txt")


def _kind(obj):
    if inspect.isclass(obj):
        return "class"
    if inspect.isfunction(obj):
        return "function"
    if inspect.ismodule(obj):
        return "module"
    return "value"


@pytest.mark.parametrize(
    "line", SNAPSHOT.read_text().splitlines(), ids=lambda l: l.split()[0]
)
def test_public_name_is_still_available(line):
    name, kind = line.split()
    assert hasattr(ec, name), f"{name} is missing"
    assert _kind(getattr(ec, name)) == kind


def test_view_module_imports_still_resolve():
    import web.view.evidence  # noqa: F401
