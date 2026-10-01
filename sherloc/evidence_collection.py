"""
Author: Sophie Stephenson
Date: 2023-03-15

Collect evidence of IPS. Basic version collects this data from the phone:

1. All apps that might be dual-use or spyware and data about them (install
    time, desc, etc.)
2. Permission usage in the last 7 days (or 28 days, if we can)

The consultation data classes live in `evidence_model`, the forms in
`evidence_forms` and the choice lists in `evidence_choices`. They are
re-exported here, so `evidence_collection.<name>` keeps working.
"""
import json
import os
import shutil
import sqlite3
from enum import Enum

import config
import jinja2
import pdfkit
from config import DUMP_DIR, REPORT_DIR, SCREENSHOT_DIR, SHERLOC_VERSION
from filelock import FileLock
from phone_scanner.db import create_mult_appinfo, create_scan
from phone_scanner.privacy_scan_android import take_screenshot
from web.view.index import get_device
from web.view.scan import first_element_or_none

from evidence_choices import (  # noqa: F401
    TMP_CONSULT_DATA_DIR,
    SCREENSHOT_FOLDER,
    CONTEXT_PKL_FNAME,
    YES_NO_DEFAULT,
    PERSON_DEFAULT,
    LEGAL_DEFAULT,
    TWO_FACTOR_DEFAULT,
    SECOND_FACTORS,
    ACCOUNTS,
    EMPTY_CHOICE,
    YES_NO_UNSURE_CHOICES,
    YES_NO_CHOICES,
    PERSON_CHOICES,
    PWD_CHOICES,
    LEGAL_CHOICES,
    DEVICE_TYPE_CHOICES,
    TWO_FACTOR_CHOICES,
    ACCOUNT_CHOICES,
)
from evidence_model import (  # noqa: F401
    Pages,
    EvidenceDataEncoder,
    Dictable,
    DictInitClass,
    AccountSection,
    SuspiciousLogins,
    PasswordCheck,
    RecoverySettings,
    TwoFactorSettings,
    SecurityQuestions,
    InstallInfo,
    PermissionInfo,
    AppInfo,
    Risk,
    RiskReport,
    TAQDevices,
    TAQAccounts,
    TAQSharing,
    TAQSmarthome,
    TAQKids,
    TAQLegal,
    Notes,
    RiskFactor,
    ConsultationData,
    AccountInvestigation,
    ScanData,
    TAQData,
    ConsultSetupData,
    ConsultNotesData,
    ScreenshotInfo,
    get_all_screenshot_files,
)
from evidence_forms import (  # noqa: F401
    NotesForm,
    PermissionForm,
    InstallForm,
    SpywareAppForm,
    DualUseAppForm,
    SuspiciousLoginsForm,
    PasswordForm,
    RecoveryForm,
    TwoFactorForm,
    SecurityQForm,
    AccountInfoForm,
    AppSelectForm,
    StartForm,
    ScanForm,
    SpywareForm,
    DualUseForm,
    SingleAppCheckForm,
    AppInvestigationForm,
    AccountCompromiseForm,
    AppSelectPageForm,
    ManualAppSelectForm,
    ManualAddPageForm,
    ScreenshotEditForm,
    MultScreenshotEditForm,
    TAQDeviceCompForm,
    TAQAccountsForm,
    TAQSharingForm,
    TAQSmartHomeForm,
    TAQKidsForm,
    TAQLegalForm,
    TAQForm,
    HomepageNoteForm,
)


def get_scan_by_ser(ser, all_scan_data: list[ScanData]):

    for scan in all_scan_data:
        if scan.serial == ser:
            return scan

    return ScanData()




def update_scan_by_ser(new_scan: ScanData, all_scan_data: list[ScanData]):
    """
    Adds new_scan to all_scan_data.
    If new_scan matches serial numbers of an existing scan, it replaces that scan.
    Otherwise, it appends the new scan to the list.
    """

    for i in range(len(all_scan_data)):
        scan = all_scan_data[i]

        # if serial numbers match, replace with the new one
        if scan.serial == new_scan.serial:
            all_scan_data[i] = new_scan
            return all_scan_data

    # Otherwise, just append the new scan
    all_scan_data.append(new_scan)
    return all_scan_data

class ConsultDataTypes(Enum):
    TAQ = 1
    SCANS = 2
    ACCOUNTS = 3
    NOTES = 4

def get_data_filename(datatype: ConsultDataTypes):

    if datatype == ConsultDataTypes.TAQ.value:
        return "taq.json"
    elif datatype == ConsultDataTypes.SCANS.value:
        return "scans.json"
    elif datatype == ConsultDataTypes.ACCOUNTS.value:
        return "accounts.json"
    else:
        return "notes.json"


def render_printout_html(context):
    """Render the printout template to an HTML string."""
    template_loader = jinja2.FileSystemLoader("./")
    # Notes, nicknames and app names are free text and wkhtmltopdf renders the
    # result, so everything is HTML-escaped.
    template_env = jinja2.Environment(loader=template_loader, autoescape=True)
    template = template_env.get_template(os.path.join('templates', 'printout.html'))
    return template.render(context)


def printout_pdf_options():
    # No 'enable-local-file-access': the page is built from user-entered text, and
    # images are fetched from the running app over http (see url_root).
    return {
        'margin-top': '15mm',
        'margin-bottom': '20mm',
        'margin-left': '10mm',
        'margin-right': '10mm',
        'footer-spacing': '5',
        'footer-center': 'Created by Madison Tech Clinic using Sherloc {} • Page [page] of [toPage]'.format(SHERLOC_VERSION),
        'footer-font-name': 'Georgia',
        'footer-font-size': '8',
    }


def create_printout(context, out_file=None):
    out_file = out_file or os.path.join('reports', 'test_report.pdf')
    css_path = os.path.join('webstatic', 'style.css')

    html_string = render_printout_html(context)

    wkhtmltopdf = shutil.which('wkhtmltopdf') or '/usr/local/bin/wkhtmltopdf'
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf)

    pdfkit.from_string(html_string, out_file, options=printout_pdf_options(), configuration=config, css=css_path, verbose=True)

    print("Printout created. Filename is", out_file)

    return out_file


def create_overall_summary(context, second_person=False):
    concerns = dict(
        spyware = [],
        dualuse = [],
        accounts = []
    )

    return concerns

def get_screenshots(context, name, dir):
    screenshots = os.listdir(dir)
    name = name.replace(' ', '')
    return list(filter(lambda x: context in x and name in x, screenshots))


def screenshot(device, fname):
    """Take a screenshot and return the file where the screenshot is"""
    fname = os.path.join(SCREENSHOT_FOLDER, fname)

    sc = get_device(device)
    ser = sc.devices()

    if device.lower() == "android":
        take_screenshot(ser, fname=fname)

    else:
        # don't know how to do this yet
        return None

    return fname

def remove_unwanted_data(data):
    """Clean data from forms (e.g., remove CSRF tokens so they don't live in the session)"""
    unwanted_keys = ["csrf_token"]

    if isinstance(data, list):
        return [remove_unwanted_data(d) for d in data]

    elif isinstance(data, dict):
        new_data = {}
        for k in data.keys():
            if k not in unwanted_keys:
                new_v = remove_unwanted_data(data[k])
                new_data[k] = new_v

        return new_data

    else:
        return data

def account_is_concerning(account):
    login_concern = account['suspicous_logins']['recognize'] != 'y' or account['suspicous_logins']['activity_log'] != 'n'
    pwd_concern = account['password_check']['guess'] != 'n' or account['password_check']['know'] != 'n'
    recovery_concern = account['recovery_settings']['phone_owned'] != 'y' or account['recovery_settings']['email_owned'] != 'y'
    twofactor_concern = account['two_factor_settings']['second_factor_owned'] != 'n'
    security_concern = account['security_questions']['know'] != 'n'

    return login_concern or pwd_concern or recovery_concern or twofactor_concern or security_concern

def get_multiple_app_details(device, ser, apps):
    filled_in_apps = []
    for app in apps:
        d = get_app_details(device, ser, app["id"])
        d["flags"] = app["flags"]
        d["appId"] = app["id"]
        filled_in_apps.append(d)
    return filled_in_apps

def get_app_details(device, ser, appid):
    sc = get_device(device)
    d, info = sc.app_details(ser, appid)

    # Copy some info over from the info dict
    # TODO: Just return this all in one clean dictionary from app_details()...
    info_things = ["install_time", "last_updated", "app_version"]
    for item in info_things:
        try:
            d[item] = info[item]
            if d[item].strip() == "":
                d[item] = ""
        except KeyError:
            d[item] = ""

    #d = d.fillna('')
    #d = d.to_dict(orient='index').get(0, {})
    #d['appId'] = appid

    return d

def get_scan_obj(device, nickname):
    """Create the scan object."""
    sc = get_device(device)
    if not sc:
        raise Exception("Please choose one device to scan.")
    if not nickname:
        raise Exception("Please give the device a nickname.")
    return sc

def get_ser_from_scan_obj(sc):
    """Get the serial number of the device, if it exists."""
    ser = sc.devices()

    print("Devices: {}".format(ser))
    if not ser:
        # FIXME: add pkexec scripts/ios_mount_linux.sh workflow for iOS if
        # needed.
        raise Exception("A device wasn't detected.")

    ser = first_element_or_none(ser)
    return ser

def get_serial(device, nickname):
    sc = get_scan_obj(device, nickname)
    ser = get_ser_from_scan_obj(sc)
    return ser


def get_scan_data(device, device_owner):

    # The following code is adapted from web/view/scan.py

    template_d = dict(
        task="home",
        title=config.TITLE,
        device=device,
        device_primary_user=config.DEVICE_PRIMARY_USER,   # TODO: Why is this sent
        apps={},
    )

    try:
        sc = get_scan_obj(device, device_owner)
        ser = get_ser_from_scan_obj(sc)

        print(">>>scanning_device", device, ser, "<<<<<")

        if device == 'ios':
            # go through pairing process and do not scan until it is successful.
            isconnected, reason = sc.setup()
            if not isconnected:
                error = "If an iPhone is connected, open iTunes, click through the "\
                        "connection dialog and wait for the \"Trust this computer\" "\
                        "prompt to pop up in the iPhone, and then scan again."
                template_d["error"] = error.format(reason)
                raise Exception(error)

        # TODO: model for 'devices scanned so far:' device_name_map['model']
        # and save it to scan_res along with device_primary_user.
        device_name_print, device_name_map = sc.device_info(serial=ser)

        # Finds all the apps in the device
        # @apps have appid, title, flags, TODO: add icon
        apps = sc.find_spyapps(serialno=ser).fillna('').to_dict(orient='index')
        if len(apps) <= 0:
            print("The scanning failed for some reason.")
            error = "The scanning failed. This could be due to many reasons. Try"\
                " rerunning the scan from the beginning. If the problem persists,"\
                " please report it in the file. Check the phone manually. Sorry for"\
                " the inconvenience."
            template_d["error"] = error
            raise Exception(error)

        clientid = "1"

        scan_d = {
            'clientid': clientid,
            'serial': config.hmac_serial(ser),
            'serial_or_udid': ser,
            'device': device,
            'device_model': device_name_map.get('model', '<Unknown>').strip(),
            'device_version': device_name_map.get('version', '<Unknown>').strip(),
            'device_primary_user': device_owner,
        }

        if device == 'ios':
            scan_d['device_manufacturer'] = 'Apple'
            scan_d['last_full_charge'] = 'unknown'
        else:
            scan_d['device_manufacturer'] = device_name_map.get(
                'brand', "<Unknown>").strip()
            scan_d['last_full_charge'] = device_name_map.get(
                'last_full_charge', "<Unknown>")

        rooted, rooted_reason = sc.isrooted(ser)
        scan_d['is_rooted'] = rooted
        scan_d['rooted_reasons'] = rooted_reason

        scanid = create_scan(scan_d)

        # if device == 'ios':
        #    pii_fpath = sc.dump_path(ser, 'Device_Info')
        #    print('Revelant info saved to db. Deleting {} now.'.format(pii_fpath))
        #    cmd = os.unlink(pii_fpath)
        #    s = catch_err(run_command(cmd), msg="Delete pii failed", cmd=cmd)
        #    print('iOS PII deleted.')

        create_mult_appinfo([(scanid, appid, json.dumps(
            info['flags']), '', '<new>') for appid, info in apps.items()])

        template_d.update(dict(
            isrooted=(
                "Maybe (this is possibly just a bug with our scanning tool). Reason(s): {}"
                .format(rooted_reason) if rooted
                else "Don't know" if rooted is None
                else "No"
            ),
            device_name=device_name_print,
            apps=apps,
            scanid=scanid,
            sysapps=set(),  # sc.get_system_apps(serialno=ser)),
            serial=ser,
            # TODO: make this a map of model:link to display scan results for that
            # scan.
            error=config.error()
        ))

        suspicious_apps = []
        other_apps = []

        for k in apps.keys():
            app = apps[k]
            app["id"] = k
            app["app_name"] = app["title"]
            if app["app_name"].strip() == "":
                app["app_name"] = k

            # Check if any suspicious flags are present and add to the suspicious list
            suspicious_flags = ['spyware',
                                'dual-use',
                                'regex-spy',
                                'offstore-spyware',
                                'co-occurrence',
                                'onstore-dual-use',
                                'offstore-app']
            if len([x for x in app["flags"] if x in suspicious_flags]) > 0:
                suspicious_apps.append(app)
            else:
                other_apps.append(app)

        detailed_suspicious_apps = get_multiple_app_details(device, ser, suspicious_apps)
        detailed_other_apps = get_multiple_app_details(device, ser, other_apps)

        return scan_d, detailed_suspicious_apps, detailed_other_apps

    except Exception as e:
        template_d["error"] = str(e)
        raise e


# Save data to the right tmp file as JSON
# Overwrites it always, assume any previous data has been incorporated
def save_data_as_json(data, datatype: ConsultDataTypes):

    json_object = json.dumps(data, cls=EvidenceDataEncoder)

    fname = os.path.join(TMP_CONSULT_DATA_DIR, get_data_filename(datatype))

    lock = FileLock(fname + ".lock")
    with lock:
        with open(fname, 'w') as outfile:
            outfile.write(json_object)

    return

def load_json_data(datatype: ConsultDataTypes):

    fname = os.path.join(TMP_CONSULT_DATA_DIR, get_data_filename(datatype))

    lock = FileLock(fname + ".lock")
    with lock:
        if not os.path.exists(fname):
            if datatype in [ConsultDataTypes.NOTES.value, ConsultDataTypes.TAQ.value]:
                return dict()
            else:
                return list()

        with open(fname, 'r') as openfile:
            json_object = json.load(openfile)
            return json_object

def load_object_from_json(datatype: ConsultDataTypes):
    json_data = load_json_data(datatype)
    if datatype == ConsultDataTypes.TAQ.value:
        return TAQData(**json_data)

    if datatype == ConsultDataTypes.ACCOUNTS.value:
        assert isinstance(json_data, list)
        return [AccountInvestigation(**acct) for acct in json_data]

    if datatype == ConsultDataTypes.SCANS.value:
        assert isinstance(json_data, list)
        return [ScanData(**scan) for scan in json_data]

    if datatype == ConsultDataTypes.NOTES.value:
        return ConsultNotesData(**json_data)

    return None

def wipe_client_database():
    """Remove every row of client data from the SQLite database.

    The schema stays so the app keeps working. Deleted content is overwritten
    (secure_delete) and the file is rewritten (VACUUM), so it cannot be
    recovered from free pages. Does nothing when the database does not exist.
    """
    path = config.SQL_DB_PATH.replace("sqlite:///", "", 1)
    if not os.path.exists(path):
        return

    con = sqlite3.connect(path)
    try:
        con.execute("PRAGMA secure_delete = ON")
        tables = [
            r[0]
            for r in con.execute(
                "select name from sqlite_master where type = 'table' "
                "and name not like 'sqlite_%' and name != 'alembic_version'"
            )
        ]
        with con:
            for table in tables:
                con.execute('delete from "{}"'.format(table.replace('"', '""')))
            if con.execute(
                "select 1 from sqlite_master where name = 'sqlite_sequence'"
            ).fetchone():
                con.execute("delete from sqlite_sequence")
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        con.execute("VACUUM")
    finally:
        con.close()


def delete_client_data():

    # Delete the consult data stored as json
    print("Deleting consultation data...")
    for datatype in ConsultDataTypes:
        fname = os.path.join(TMP_CONSULT_DATA_DIR, get_data_filename(datatype.value))
        if os.path.exists(fname):
            os.remove(fname)

    # Delete phone dumps
    print("Deleting phone dumps...")
    print(DUMP_DIR)
    shutil.rmtree(DUMP_DIR, ignore_errors=True)
    os.makedirs(DUMP_DIR, exist_ok=True)

    # Delete screenshots
    print("Deleting screenshots...")
    print(SCREENSHOT_DIR)
    shutil.rmtree(SCREENSHOT_DIR, ignore_errors=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # Delete report
    print("Deleting report...")
    print(REPORT_DIR)
    shutil.rmtree(REPORT_DIR, ignore_errors=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    # Delete everything stored in the database
    print("Deleting database records...")
    wipe_client_database()

    print("Client data deleted.")
