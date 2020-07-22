from flask import Flask


# For the automatic scheduling of task ending
from flask_apscheduler import APScheduler

# For the LDAP Authentication
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

from flask_login import LoginManager

from flask_migrate import Migrate

from flask_app.src.global_stuff import DEBUG_MODE

# # for Logging
from flask_app.src.custom_logs import LogSetup
from flask_app.config import Config


# from flask_app.src import sql_sqlalchemy as mydb


app = Flask(__name__, static_folder="templates/static")



app.config.from_object(Config)

# naming convention required to use migration with SQLite...
# see https://github.com/miguelgrinberg/Flask-Migrate/issues/61
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# DB stuff
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
db.init_app(app)
 
# megazordDB = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)

# Handles current apps and current users
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'app_routes.login'

# To schedule jobs
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Handles logging of outputs
if not DEBUG_MODE:
    logs = LogSetup()
    logs.init_app(app)

from flask_app.src.app_routes import app_routes
app.register_blueprint(app_routes)

from flask_app.src import models

# import flask_app.src.shell_config

# dbldap.create_all()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': models.User, 'Host': models.Host, 'Component': models.Component, 'Reservation_type': models.Reservation_type, 'Reservation': models.Reservation}

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0')
    except Exception as e:
        print(e)