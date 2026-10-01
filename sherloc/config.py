import hashlib
import hmac
import logging
import logging.handlers as handlers
import os
import secrets
import shlex
from datetime import datetime
from pathlib import Path
from sys import platform

from inputcheck import validate_path_part

SHERLOC_VERSION = "1.1.4"

def setup_logger():
    """
    Set up a logger with a rotating file handler.

    The logger will write in a file named 'app.log' in the 'logs' directory.
    The log file will rotate when it reaches 100,000 bytes, keeps a maximum of 30 files.

    Returns:
        logging.Logger: The configured logger object.
    """
    handler = handlers.RotatingFileHandler(
        "../logs/app.log", maxBytes=100000, backupCount=30
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


DEV_SUPPRTED = ["android", "ios"]  # 'windows', 'mobileos', later
THIS_DIR = Path(__file__).absolute().parent

# Used by data_process only.
source_files = {
    "playstore": "static_data/android_apps_crawl.csv.gz",
    "appstore": "static_data/ios_apps_crawl.csv.gz",
    "offstore": "static_data/offstore_apks.csv",
}
spyware_list_file = "static_data/spyware.csv"  # hand picked


# ---------------------------------------------------------
DEBUG = bool(int(os.getenv("DEBUG", "0")))
TEST = bool(int(os.getenv("TEST", "0")))

# The app handles sensitive evidence and has no login, so it listens on the
# loopback interface only. Set SHERLOC_HOST to change that, and list the host
# names clients will use in SHERLOC_ALLOWED_HOSTS (comma separated).
HOST = os.getenv("SHERLOC_HOST", "127.0.0.1")
ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"} | {
    h.strip().lower()
    for h in os.getenv("SHERLOC_ALLOWED_HOSTS", "").split(",")
    if h.strip()
}

DEVICE_PRIMARY_USER = {
    "me": "Me",
    "child": "A child of mine",
    "partner": "My current partner/spouse",
    "family_other": "Another family member",
    "other": "Someone else",
}

ANDROID_PERMISSIONS_CSV = "static_data/android_permissions.csv"
IOS_DUMPFILES = {
    "Jailbroken-FS": "ios_jailbroken.log",
    "Jailbroken-SSH": "ios_jailbreak_ssh.retcode",
    "Apps": "ios_apps.json",
    "Info": "ios_info.xml",
}

TEST_APP_LIST = "static_data/android.test.apps_list"
# TITLE = "Anti-IPS: Stop Intimate Partner Surveillance"

TITLE = {"title": "Sherloc{}".format(" (test)" if TEST else "")}


APP_FLAGS_FILE = "static_data/app-flags.csv"
APP_INFO_SQLITE_FILE = "sqlite:///static_data/app-info.db"

# IOC stalkware indicators
IOC_PATH = "stalkerware-indicators"
IOC_FILE = os.path.join(IOC_PATH, "ioc.yaml")

# we will resolve the database path using an absolute path to __FILE__ because
# there are a couple of sources of truth that may disagree with their "path
# relavitity". Needless to say, FIXME
SQL_DB_PATH = f"sqlite:///{str(THIS_DIR / 'data/fieldstudy.db')}"
# SQL_DB_CONSULT_PATH = 'sqlite:///data/consultnotes.db' + ("~test" if TEST else "")


def set_test_mode(test):
    """
    Sets the test mode to the given value and returns the new values of APP_FLAGS_FILE and SQL_DB_PATH.
    """
    app_flags_file, sql_db_path = APP_FLAGS_FILE, SQL_DB_PATH
    if test:
        if not app_flags_file.endswith("~test"):
            app_flags_file = APP_FLAGS_FILE + "~test"
        if not sql_db_path.endswith("~test"):
            sql_db_path = sql_db_path + "~test"
    else:
        if app_flags_file.endswith("~test"):
            app_flags_file = app_flags_file.replace("~test", "")
        if sql_db_path.endswith("~test"):
            sql_db_path = sql_db_path.replace("~test", "")
    return app_flags_file, sql_db_path


APP_FLAGS_FILE, SQL_DB_PATH = set_test_mode(TEST)


STATIC_DATA = THIS_DIR / "static_data"

# TODO: We should get rid of this, ADB_PATH is very confusing
ANDROID_HOME = os.getenv("ANDROID_HOME", "")
PLATFORM = (
    "darwin"
    if platform == "darwin"
    else (
        "linux"
        if platform.startswith("linux")
        else "win32" if platform == "win32" else None
    )
)

ADB_PATH = shlex.quote(os.path.join(ANDROID_HOME, "adb"))

# LIBIMOBILEDEVICE_PATH = shlex.quote(str(STATIC_DATA / ("libimobiledevice-" + PLATFORM)))
LIBIMOBILEDEVICE_PATH = ""
# MOBILEDEVICE_PATH = 'mobiledevice'
# MOBILEDEVICE_PATH = os.path.join(THISDIR, "mdf")  #'python2 -m MobileDevice'
if PLATFORM:
    MOBILEDEVICE_PATH = shlex.quote(str(STATIC_DATA / ("ios-deploy-" + PLATFORM)))
else:
    MOBILEDEVICE_PATH = shlex.quote(str(STATIC_DATA / ("ios-deploy-none")))

DUMP_DIR = THIS_DIR / "phone_dumps"
SCRIPT_DIR = THIS_DIR / "scripts"
REPORT_DIR = THIS_DIR / "reports"
SCREENSHOT_DIR = THIS_DIR / "webstatic" / "images" / "screenshots"

DATE_STR = "%Y-%m-%d %I:%M %p"
ERROR_LOG = []

APPROVED_INSTALLERS = {"com.android.vending", 
                       "com.sec.android.preloadinstaller", 
                       "com.sec.android.app.samsungapps"}

REPORT_PATH = THIS_DIR / "reports"
PII_KEY_PATH = STATIC_DATA / "pii.key"

# SHA-256 of key files that were committed to the public repository before
# they were untracked. Anyone can read those values, so a key file that still
# holds one of them is replaced. Only hashes are kept here.
KNOWN_PUBLIC_KEY_SHA256 = {
    "d6ad5dae593a9e058698c0ffc2f4da9c865d1a0e1ed09c9246dd446eb1304e86",  # pii.key
    "eb7e855e3840deca9c4a9882e8a124e44c098f82a670aec10c0b7ea23ad4c6ea",  # flask.secret
}


def open_or_create_random_key(fpath, keylen=32):
    """
    Returns the key stored at `fpath`, creating it first if needed.

    The key is replaced when the file is missing, has the wrong length, or holds
    a value that was once committed to the public repository. New files are
    readable by the owner only.

    Args:
        fpath (str or Path): The path to the file.
        keylen (int, optional): The length of the random key. Defaults to 32.

    Returns:
        bytes: The key.
    """
    fpath = Path(fpath)

    if fpath.exists():
        key = fpath.read_bytes()
        if (
            len(key) == keylen
            and hashlib.sha256(key).hexdigest() not in KNOWN_PUBLIC_KEY_SHA256
        ):
            return key

    key = secrets.token_bytes(keylen)
    fd = os.open(fpath, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(key)
    return key


FLASK_SECRET_PATH = STATIC_DATA / "flask.secret"

# Keys are created on first use, not when this module is imported, so scripts
# and tests that only read a setting do not write key files.
_LAZY_KEYS = {
    "PII_KEY": lambda: open_or_create_random_key(PII_KEY_PATH, keylen=32),
    "FLASK_SECRET": lambda: open_or_create_random_key(FLASK_SECRET_PATH),
}
_key_cache = {}


def __getattr__(name):
    """Module attribute hook (PEP 562): PII_KEY and FLASK_SECRET."""
    if name in _LAZY_KEYS:
        if name not in _key_cache:
            _key_cache[name] = _LAZY_KEYS[name]()
        return _key_cache[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def ensure_dirs():
    """Create the folders the app writes to. Called when the app starts."""
    REPORT_PATH.mkdir(exist_ok=True)


def hmac_serial(ser: str) -> str:
    """Returns a string starting with HSN_<hmac(ser)>. If ser already have 'HSN_',
    it returns the same value."""
    if ser.startswith("HSN_"):
        return ser
    hser = hmac.new(__getattr__("PII_KEY"), ser.encode("utf8"), digestmod=hashlib.sha256).hexdigest()
    return f"HSN_{hser}"


def add_to_error(*args):
    global ERROR_LOG
    m = "\n".join(str(e) for e in args)
    print(m)
    ERROR_LOG.append(m)


def error():
    global ERROR_LOG
    e = ""
    if len(ERROR_LOG) > 0:
        e, ERROR_LOG = ERROR_LOG[0], ERROR_LOG[1:]

        print(f"ERROR: {e}")
    return e.replace("\n", "<br/>")

def create_screenshot_fname(context, serial="misc"):
    """Return a new screenshot path, creating its directory.

    `context` and `serial` can come from a URL, so each must be a single safe
    path component and the result must stay inside the screenshots directory.
    """
    subfolder = validate_path_part(context.replace(" ", ""), "screenshot context")
    serial = validate_path_part(serial, "serial")

    root = os.path.realpath(os.path.join(THIS_DIR, "webstatic", "images", "screenshots"))
    dir_path = os.path.realpath(os.path.join(root, serial, subfolder))
    if os.path.commonpath([root, dir_path]) != root:
        raise ValueError("Invalid screenshot location.")
    os.makedirs(dir_path, exist_ok=True)

    # Create a filename with the current time and context
    curr_time = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
    fname = os.path.join(dir_path, curr_time + '.png')

    print("This is the filename: {}".format(fname))

    return fname
