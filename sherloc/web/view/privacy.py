import hashlib
import hmac
import os
import random
import re
import shlex
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime

from flask import render_template, request, url_for

import config

#from isdi.scanner import iosScreenshot
from isdi.scanner.privacy_scan_android import do_privacy_check, take_screenshot
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
    print(f"ser={ser}, context={context}, cmd={cmd}")
    outf = config.create_screenshot_fname(context, ser)
    if device == "ios":
        res = iosScreenshot(ser, outf, nocache=True)
    else:
        res = do_privacy_check(ser, cmd, outf)
    print(f"Screenshot Taken: {outf}")
    return res

def iosScreenshot(ser, fname, nocache = False):
    linkPro = subprocess.Popen(["pymobiledevice3", "lockdown", "start-tunnel"], stdout= subprocess.PIPE)
    time.sleep(2)
    output = linkPro.stdout
    rsdAddress = ""
    rsdPort = ""
    i = 0
    for lineByte in output:
        line = lineByte.decode('utf-8')
        print(line)
        if i == 6:
            break
        if "RSD Address" in line:
            rsdAddress = line[13:]
        if "RSD Port" in line:
            lineSplit = line.split(":")
            rsdPort = lineSplit[1][1:]
        i += 1
    command = "pymobiledevice3 developer dvt screenshot " + fname + " --rsd " + rsdAddress + " " + rsdPort

    try:
        subprocess.run(shlex.split(command), check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}: {e.output}")
        return "<div class='screenshotfail'>Screenshot failed with exit code {}</div>".format(e.returncode)
    except Exception as e:
        print(e)
        return "<div class='screenshotfail'>Screenshot failed with exception {}</div>".format(e)

    return "<img height='400px' src='" + url_for('static', filename=fname.split("webstatic/", 1)[-1]) + "'/>"
