"""Validation for values that end up in shell commands or file paths.

Device serials come from HTTP requests and from the connected device, and app
ids come from HTTP requests. None of them are trusted. Anything that does not
match the narrow patterns below is rejected before a command is built.

Error messages never include the rejected value, because the message can be
shown in a page.
"""

import re

# Android serials, iOS UDIDs, adb network targets (host:port), and the
# HSN_<hmac> form that Sherloc uses for stored serials.
_SERIAL = re.compile(r"[A-Za-z0-9._:-]{1,128}")
# Android package names and iOS bundle identifiers.
_APPID = re.compile(r"[A-Za-z0-9._-]{1,255}")
# A single directory or file name component.
_PATH_PART = re.compile(r"[A-Za-z0-9._-]{1,128}")


def _check(value, pattern, what):
    if (
        not isinstance(value, str)
        or pattern.fullmatch(value) is None
        or set(value) == {"."}
    ):
        raise ValueError(f"Invalid {what}.")
    return value


def validate_serial(value):
    """Return `value` if it is a plausible device serial, else raise ValueError."""
    return _check(value, _SERIAL, "device serial")


def validate_appid(value):
    """Return `value` if it is a plausible app id, else raise ValueError."""
    return _check(value, _APPID, "app id")


def validate_path_part(value, what="path component"):
    """Return `value` if it is safe as one path component, else raise ValueError.

    Rejects separators, quotes, whitespace, and the names "." and "..".
    """
    return _check(value, _PATH_PART, what)
