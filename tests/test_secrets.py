"""Secrets must not be committed, and key files must be created safely."""

import hashlib
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

import config

REPO_ROOT = Path(__file__).resolve().parent.parent
KEY_SUFFIXES = (".key", ".secret", ".pem")


def _tracked_files():
    if shutil.which("git") is None:
        pytest.skip("git is not available")
    r = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    if r.returncode != 0:
        pytest.skip("not a git work tree")
    return r.stdout.splitlines()


def test_no_key_material_is_tracked_by_git():
    offenders = [f for f in _tracked_files() if f.lower().endswith(KEY_SUFFIXES)]
    assert offenders == []


def test_key_paths_are_gitignored():
    if shutil.which("git") is None:
        pytest.skip("git is not available")
    for path in (config.PII_KEY_PATH, config.FLASK_SECRET_PATH):
        rel = Path(path).resolve().relative_to(REPO_ROOT)
        r = subprocess.run(["git", "check-ignore", "-q", str(rel)], cwd=REPO_ROOT)
        assert r.returncode == 0, f"{rel} is not ignored"


def test_new_key_has_requested_length_and_is_private(tmp_path):
    p = tmp_path / "k.key"
    key = config.open_or_create_random_key(p, keylen=32)
    assert len(key) == 32
    assert p.read_bytes() == key
    if os.name == "posix":
        assert stat.S_IMODE(p.stat().st_mode) == 0o600


def test_existing_key_is_reused(tmp_path):
    p = tmp_path / "k.key"
    first = config.open_or_create_random_key(p, keylen=32)
    assert config.open_or_create_random_key(p, keylen=32) == first


@pytest.mark.parametrize("size", [0, 5, 31, 33, 64])
def test_key_file_with_wrong_length_is_replaced(tmp_path, size):
    p = tmp_path / "k.key"
    p.write_bytes(b"\x01" * size)
    key = config.open_or_create_random_key(p, keylen=32)
    assert len(key) == 32
    assert p.read_bytes() == key


def test_key_that_was_once_committed_is_replaced(tmp_path, monkeypatch):
    p = tmp_path / "k.key"
    old = b"\x07" * 32
    p.write_bytes(old)
    monkeypatch.setattr(
        config, "KNOWN_PUBLIC_KEY_SHA256", {hashlib.sha256(old).hexdigest()}
    )
    key = config.open_or_create_random_key(p, keylen=32)
    assert key != old
    assert p.read_bytes() == key


def test_the_real_committed_keys_are_listed_as_public():
    # The two key files that were committed to the public repository. Their
    # hashes (not values) are recorded so they are never used again.
    assert len(config.KNOWN_PUBLIC_KEY_SHA256) >= 2
