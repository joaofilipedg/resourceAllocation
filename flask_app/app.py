import secrets
from flask import Flask
from flask_app.src import sql_sqlalchemy as mydb
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# For the automatic scheduling of task ending
from flask_apscheduler import APScheduler

# For the LDAP Authentication
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__, static_folder="templates/static")

class Config(object):
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:///sqlite_db/flask_scheduler_context.db')
    }

    SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/test.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_SECRET_KEY = secrets.token_urlsafe(16)
    LDAP_PROVIDER_URL = "ldaps://auth.inesc-id.pt/"
    LDAP_PROTOCOL_VERSION = 3

app.config.from_object(Config())

dbldap = SQLAlchemy(app)

app.secret_key = secrets.token_urlsafe(16)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

from flask_app.src.sql_sqlalchemy import dbmain

from flask_app.auth.views import auth
app.register_blueprint(auth)

dbldap.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0')
    