"""Command-line mode flags that must be applied before `config` is imported."""


def apply_cli_mode(argv, environ):
    """Set TEST=1 in `environ` when `test` is on the command line.

    `config` reads TEST when it is imported, and other modules read paths from
    `config` at import time, so this has to run first. Returns True when test
    mode was requested.
    """
    if {"TEST", "test"} & set(argv[1:]):
        environ["TEST"] = "1"
        return True
    return False
