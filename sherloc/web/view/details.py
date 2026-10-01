from flask import abort, request, render_template
from web import app
from web.view import get_device
import config
from inputcheck import validate_appid, validate_serial


@app.route("/details/app/<device>", methods=["GET"])
def app_details(device):
    appid = request.args.get("appId")
    ser = request.args.get("serial")
    try:
        validate_appid(appid)
        validate_serial(ser)
    except ValueError:
        return "Invalid app id or device serial.", 400
    sc = get_device(device)
    if sc is None:
        abort(404)
    d, info = sc.app_details(ser, appid)
    d["appId"] = appid

    # detect apple and put the key into d.permissions
    # if "Ios" in str(type(sc)):
    #    print("apple iphone")
    # else:
    #    print(type(sc))

    print(d.keys())
    return render_template(
        "main.html",
        task="app",
        title=config.TITLE,
        device_primary_user=config.DEVICE_PRIMARY_USER,
        app=d,
        info=info,
        device=device,
    )
