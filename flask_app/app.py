from flask import Flask


# For the automatic scheduling of task ending
from flask_apscheduler import APScheduler

# For the LDAP Authentication
from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager

from flask_app.src.global_stuff import DEBUG_MODE

# # for Logging
from flask_app.src.custom_logs import LogSetup
from flask_app.config import Config


# from flask_app.src import sql_sqlalchemy as mydb


app = Flask(__name__, static_folder="templates/static")



app.config.from_object(Config)

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