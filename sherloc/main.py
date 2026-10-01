#!/usr/bin/env python3
"""
The mainfile of ISDi repo.
"""
import os
import sys
import webbrowser
from threading import Timer

from runmode import apply_cli_mode

# Must run before `config` is imported: config reads TEST at import time.
apply_cli_mode(sys.argv, os.environ)

import config  # noqa: E402
from phone_scanner import db
from web import app, sa

PORT = 6200 if not (config.TEST or config.DEBUG) else 6202
HOST = config.HOST

def open_browser():
    """Opens a browser to make it easy to navigate to ISDi
    """
    if not config.TEST:
        webbrowser.open('http://127.0.0.1:' + str(PORT), new=0, autoraise=True)


if __name__ == "__main__":
    if config.TEST:
        print("Running in test mode.")
        print(f"App flags: {config.APP_FLAGS_FILE}\n"
              f"SQL_DB: {config.SQL_DB_PATH}")

    print(f"TEST={config.TEST}")
    db.init_db(app, sa, force=config.TEST)
    config.setup_logger()
    Timer(1, open_browser).start()
    app.run(host=HOST, port=PORT, debug=config.DEBUG, use_reloader=config.DEBUG)

    # Use this to delete client data on exit
    #atexit.register(delete_client_data)
