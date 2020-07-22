
import os
from datetime import timedelta

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from flask_app.src.global_stuff import DEBUG_MODE

basedir = os.path.abspath(os.path.dirname(__file__))

# print(basedir)
class Config(object):
    # JOB SCHEDULER STUFF
    SCHEDULER_JOBSTORES = {
        "default": SQLAlchemyJobStore(url="sqlite:///"  + os.path.join(basedir, "../sqlite/db/flask_scheduler_context.db"))
    }


    # SQLALCHEMY STUFF
    # SQLALCHEMY_DATABASE_URI             = "sqlite:////tmp/test.db"
    SQLALCHEMY_DATABASE_URI             = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(basedir, "../sqlite/db/app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS      = False
    SECRET_KEY                          = os.environ.get("SECRET_KEY") or b'\xcc\x12q\x9c\xca\xaa\xa18\xe3o\x99\xef\xe0~H\x19'

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


