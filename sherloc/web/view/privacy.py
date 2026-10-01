import hashlib
import hmac
import os
import random
import re
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime

from flask import render_template, request, url_for

import config
from inputcheck import validate_path_part, validate_serial

#from phone_scanner import iosScreenshot
from phone_scanner.privacy_scan_android import do_privacy_check, take_screenshot
from web import app
from web.view.index import get_device


@app.route("/privacy", methods=["GET"])
def privacy():
    """
    TODO: Privacy scan. Think how should it flow.
    Privacy is a seperate page.
    """
    return render_template(
        "main.html",
        task="privacy",
        device_primary_user=config.DEVICE_PRIMARY_USER,
        title=config.TITLE,
    )


@app.route("/privacy/<device>/<cmd>/<context>/<ser>", methods=["GET"])
def privacy_scan(device, cmd, context, ser):
    try:
        validate_serial(ser)
        validate_path_part(context.replace(" ", ""), "screenshot context")
    except ValueError:
        return "Invalid request.", 400
    print(ser)
    if device == "ios":
        res = iosScreenshot(ser, context, nocache=True)
    else:
        res = do_privacy_check(ser, cmd, context)
    print("Screenshot Taken")
    return res

def _read_rsd(lines):
    """Return (address, port) from `pymobiledevice3 lockdown start-tunnel` output."""
    address = port = ""
    for raw in lines:
        line = raw.decode("utf-8", errors="replace").strip()
        print(line)
        if line.startswith("RSD Address:"):
            address = line.split(":", 1)[1].strip()
        elif line.startswith("RSD Port:"):
            port = line.split(":", 1)[1].strip()
        if address and port:
            break
    return address, port


def iosScreenshot(ser, context, nocache = False):
    fname = config.create_screenshot_fname(context, ser)
    tunnel = subprocess.Popen(["pymobiledevice3", "lockdown", "start-tunnel"], stdout=subprocess.PIPE)
    try:
        time.sleep(2)
        rsdAddress, rsdPort = _read_rsd(tunnel.stdout)
        if not (rsdAddress and rsdPort):
            return "<div class='screenshotfail'>Screenshot failed: could not open a tunnel to the device</div>"

        # A list, not a string split on spaces: the file name can contain spaces.
        command = ["pymobiledevice3", "developer", "dvt", "screenshot", fname,
                   "--rsd", rsdAddress, rsdPort]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}: {e.output}")
            return "<div class='screenshotfail'>Screenshot failed with exit code {}</div>".format(e.returncode)
        except Exception as e:
            print(e)
            return "<div class='screenshotfail'>Screenshot failed with exception {}</div>".format(e)
    finally:
        # The tunnel keeps running until it is stopped.
        tunnel.terminate()
        try:
            tunnel.wait(timeout=5)
        except Exception:
            tunnel.kill()

    return "<img height='400px' src='" + url_for('static', filename=fname.split("webstatic/", 1)[-1]) + "'/>"
