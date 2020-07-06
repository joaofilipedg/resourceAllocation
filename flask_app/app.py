import secrets
from flask import Flask
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# For the automatic scheduling of task ending
from flask_apscheduler import APScheduler
# For the LDAP Authentication
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from flask_app.src.global_stuff import DEBUG_MODE

# # for Logging
from flask_app.src.custom_logs import LogSetup

from flask_app.src import sql_sqlalchemy as mydb

app = Flask(__name__, static_folder="templates/static")

class Config(object):
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:///sqlite/db/flask_scheduler_context.db')
    }

    SQLALCHEMY_DATABASE_URI         = "sqlite:////tmp/test.db"
    SQLALCHEMY_TRACK_MODIFICATIONS  = False
    WTF_CSRF_SECRET_KEY             = secrets.token_urlsafe(16)
    LDAP_PROVIDER_URL               = "ldaps://auth.inesc-id.pt/"
    LDAP_PROTOCOL_VERSION           = 3

    if not DEBUG_MODE:
        # Logging Setup - This would usually be stuffed into a settings module
        # Default output is a Stream (stdout) handler, also try out "watched" and "file"
        LOG_TYPE                        = "file"
        LOG_LEVEL                       = "DEBUG"

        # File Logging Setup
        LOG_DIR                         = "logs/"
        APP_LOG_NAME                    = "app.log"
        WWW_LOG_NAME                    = "www.log"
        LOG_MAX_BYTES                   = 100_000_000  # 100MB in bytes
        LOG_COPIES                      = 5

app.config.from_object(Config())

dbldap = SQLAlchemy(app)

app.secret_key = secrets.token_urlsafe(16)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'app_routes.login'

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

if not DEBUG_MODE:
    logs = LogSetup()
    logs.init_app(app)

from flask_app.src.app_routes import app_routes as app_routes_blueprint
app.register_blueprint(app_routes_blueprint)

dbldap.create_all()

# import logging
# # import traceback
# from flask_app.src.functions import full_exc_info
# try:
#     raise Exception('Dummy')
# except Exception as e:
#     # print(e)
#     # traceback.print_exc()
#     logging.critical("Something awful happened", exc_info=True)
#     # logging.critical("Something awful happened: {}".format(e))
#     # print(2)


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0')
    except Exception as e:
        print(e)