from flask import request, session
import config
from inputcheck import validate_appid, validate_serial
from web import app
from phone_scanner.db import (
    get_serial_from_db,
    save_note,
    update_appinfo,
    update_mul_appinfo,
    create_report,
    get_device_from_db,
)
from web.view.index import get_device


@app.route("/saveapps/<scanid>", methods=["POST"])
def record_applist(scanid):
    device = get_device_from_db(scanid)
    sc = get_device(device)
    d = request.form
    update_mul_appinfo([(remark, scanid, appid) for appid, remark in d.items()])
    return "Success", 200


@app.route("/savescan/<scanid>", methods=["POST"])
def record_scanres(scanid):
    device = get_device_from_db(scanid)
    sc = get_device(device)
    note = request.form.get("notes")
    r = save_note(scanid, note)
    create_report(session["clientid"])
    # create_report(request.form.get('clientid'))
    return is_success(
        r, "Success!", "Could not save the form. See logs in the terminal."
    )


@app.route("/delete/app/<scanid>", methods=["POST"])
def delete_app(scanid):
    appid = request.form.get("appid")
    try:
        validate_appid(appid)
    except ValueError:
        return "Invalid app id.", 400
    device = get_device_from_db(scanid)
    # The database only holds the pseudonymized serial, so the real serial
    # comes from the page. It is accepted only if it is the device that this
    # scan was made on.
    serial = request.form.get("serial", "")
    try:
        validate_serial(serial)
    except ValueError:
        return "Invalid device serial.", 400
    if serial.startswith("HSN_") or config.hmac_serial(serial) != get_serial_from_db(scanid):
        return "That device is not the one this scan was made on.", 400
    sc = get_device(device)
    remark = request.form.get("remark")
    action = "delete"
    # TODO: Record the uninstall and note
    r = sc.uninstall(serial=serial, appid=appid)
    if r:
        r = update_appinfo(scanid=scanid, appid=appid, remark=remark, action=action)
        print("Update appinfo failed! r={}".format(r))
    else:
        print("Uninstall failed. r={}".format(r))
    return is_success(r, "Success!", config.error())


def is_success(b, msg_succ="", msg_err=""):
    if b:
        return msg_succ if msg_succ else "Success!", 200
    else:
        return msg_err if msg_err else "Failed", 401
