import os
from datetime import timedelta
from flask import Flask

# For the DB stuff
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
    # JOB SCHEDULER STUFF
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:///sqlite/db/flask_scheduler_context.db')
    }


    # SQLALCHEMY STUFF
    SQLALCHEMY_DATABASE_URI             = "sqlite:////tmp/test.db"
    SQLALCHEMY_TRACK_MODIFICATIONS      = False
    SECRET_KEY                          = os.environ.get('SECRET_KEY') or b'\xcc\x12q\x9c\xca\xaa\xa18\xe3o\x99\xef\xe0~H\x19'

    # LDAP STUFF
    LDAP_PROVIDER_URL                   = "ldaps://auth.inesc-id.pt/"
    LDAP_PROTOCOL_VERSION               = 3
    
    # COOKIES STUFF
    SESSION_COOKIE_SECURE               = True
    REMEMBER_COOKIE_SECURE              = True
    # SESSION_COOKIE_DOMAIN               = ".example.com"

    # make connection timeout if user is idle for 5 minutes
    PERMANENT_SESSION_LIFETIME          =  timedelta(minutes=5) 

    if not DEBUG_MODE:
        # Logging Setup 
        # Default output is file but can also accet Stream (stdout) handler or "watched"
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


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0')
    except Exception as e:
        print(e)