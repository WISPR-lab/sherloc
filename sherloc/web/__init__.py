from datetime import datetime, timedelta
from time import strftime
import logging
import os
import config
from flask import Flask, g, session, request
from flask_sqlalchemy import model, SQLAlchemy
from flask_migrate import Migrate
from htmlclean import clean_description
from web.security import register_request_guards

app = Flask(__name__, static_folder="../webstatic", template_folder="../templates/")
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQL_DB_PATH
# Echoed statements include client notes and device serials.
app.config["SQLALCHEMY_ECHO"] = bool(int(os.getenv("SHERLOC_SQL_ECHO", "0")))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = config.FLASK_SECRET  # doesn't seem to be necessary
app.config["SECRET_KEY"] = config.FLASK_SECRET  # doesn't seem to be necessary
app.config["SESSION_TYPE"] = "filesystem"
sa = SQLAlchemy(app)
Migrate(app, sa)

register_request_guards(app)
app.jinja_env.filters["clean_html"] = clean_description

logger = logging.getLogger(__name__)

import web.view


@app.before_request
def make_session_permanent():
    session.permanent = True
    # expires at midnight of new day
    app.permanent_session_lifetime = (datetime.now() + timedelta(days=1)).replace(
        hour=0, minute=0, second=0
    ) - datetime.now()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.after_request
def after_request(response):
    """Logging after every request."""
    # This avoids the duplication of registry in the log,
    # since that 500 is already logged via @app.errorhandler.
    if response.status_code != 500:
        ts = strftime("[%Y-%b-%d %H:%M]")
        logger.error(
            "%s %s %s %s %s %s",
            ts,
            request.remote_addr,
            request.method,
            request.scheme,
            # The route pattern, not the URL: paths and query strings carry
            # device serials and app ids.
            request.url_rule.rule if request.url_rule else "-",
            response.status,
        )
    return response
