"""Request guards for a web app that only the local consultant should use.

Two attacks matter even when the server listens on 127.0.0.1:

* A web page the consultant has open can make their browser send requests to
  the app (cross-site request forgery). Several routes change state or run
  device commands on a plain GET.
* DNS rebinding lets a remote site read responses by getting its own hostname
  to resolve to 127.0.0.1. Rejecting unknown Host headers stops that.
"""

from urllib.parse import urlsplit

from flask import abort, request

import config

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
# Values a browser sends when the request came from the app itself, or from the
# person typing a URL or using a bookmark.
TRUSTED_FETCH_SITES = {"same-origin", "none"}


def _hostname(value):
    """Return the lowercase host without port or brackets, or None."""
    if not value:
        return None
    try:
        return urlsplit("//" + value).hostname
    except ValueError:
        return None


def _origin_hostname(origin):
    try:
        return urlsplit(origin).hostname
    except ValueError:
        return None


def register_request_guards(app):
    @app.before_request
    def _guard_request():
        if _hostname(request.host) not in config.ALLOWED_HOSTS:
            abort(403)

        fetch_site = request.headers.get("Sec-Fetch-Site")
        if fetch_site is not None and fetch_site not in TRUSTED_FETCH_SITES:
            abort(403)

        origin = request.headers.get("Origin")
        if (
            origin is not None
            and request.method not in SAFE_METHODS
            and _origin_hostname(origin) not in config.ALLOWED_HOSTS
        ):
            abort(403)
