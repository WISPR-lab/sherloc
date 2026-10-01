"""A mutable default argument is created once and shared by every call."""

import ast
import shutil
from pathlib import Path

import pytest

import web  # noqa: F401  (import order: web first avoids a circular import)
import evidence_collection as ec

SRC = Path(__file__).resolve().parent.parent / "sherloc"
MUTABLE_CALLS = {"list", "dict", "set"}


def _mutable(node):
    return isinstance(node, (ast.List, ast.Dict, ast.Set)) or (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in MUTABLE_CALLS
        and not node.args
        and not node.keywords
    )


def _offenders():
    out = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                defaults = fn.args.defaults + [d for d in fn.args.kw_defaults if d]
                for d in defaults:
                    if _mutable(d):
                        out.append(f"{path.relative_to(SRC)}:{d.lineno}")
    return out


def test_no_function_has_a_mutable_default_argument():
    assert _offenders() == []


@pytest.mark.parametrize("cls", [ec.DictInitClass, ec.AccountSection])
def test_dict_init_classes_accept_no_argument(cls):
    cls()


def test_app_info_without_arguments_builds_its_parts():
    a = ec.AppInfo()
    assert isinstance(a.notes, ec.Notes)
    assert a.flags == []


def test_app_info_still_uses_passed_values():
    a = ec.AppInfo(permissions=["p"], flags=["f", ""])
    assert a.flags == ["f"]
    assert a.permission_info.permissions == ["p"]


def test_two_consultations_do_not_share_lists():
    # Consultation-level objects take list and dict arguments with defaults.
    import inspect

    for name, obj in vars(ec).items():
        if inspect.isclass(obj) and obj.__module__ == ec.__name__:
            sig = inspect.signature(obj.__init__)
            for p in sig.parameters.values():
                assert not isinstance(p.default, (list, dict, set)), f"{name}.{p.name}"


def _data_classes():
    import enum
    import inspect

    from flask_wtf import FlaskForm

    for name, obj in vars(ec).items():
        if not (inspect.isclass(obj) and obj.__module__ == ec.__name__):
            continue
        if issubclass(obj, (FlaskForm, enum.Enum, ec.json.JSONEncoder)):
            continue
        params = inspect.signature(obj.__init__).parameters.values()
        needs_args = [
            p for p in params
            if p.name != "self" and p.default is p.empty
            and p.kind not in (p.VAR_KEYWORD, p.VAR_POSITIONAL)
        ]
        if not needs_args:
            marks = []
            if name == "ScreenshotInfo" and shutil.which("exiftool") is None:
                marks.append(pytest.mark.skip(reason="exiftool is not installed"))
            yield pytest.param(obj, id=name, marks=marks)


@pytest.mark.parametrize("cls", list(_data_classes()))
def test_every_data_class_can_be_built_without_arguments(cls):
    # Each default is now created inside __init__, so a local name that
    # shadows `dict` or `list` would fail here with UnboundLocalError.
    cls()
