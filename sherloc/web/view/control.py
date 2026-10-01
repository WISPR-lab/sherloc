import os
import signal
from threading import Timer

from flask import request
from web import app


def stop_server():
    """Interrupt this process shortly after the response has been sent.

    Werkzeug 2.1 and later no longer provide `werkzeug.server.shutdown`, so
    the old shutdown hook always failed.
    """
    Timer(0.5, lambda: os.kill(os.getpid(), signal.SIGINT)).start()


@app.route("/kill", methods=["POST"])
def killme():
    stop_server()
    return "The app has been closed! You can close this tab."
