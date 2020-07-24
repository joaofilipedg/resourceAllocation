from flask import render_template, current_app
from flask_login import current_user, login_required

from flask_app.src.models.sql_query import get_listCurrentReservations

from . import app_routes


@app_routes.route("/home")
@login_required
def home():
    username = current_user.username
    log_args = {"app": current_app, "user": username}
    list_res = get_listCurrentReservations(username=username, log_args=log_args)

    return render_template("layouts/home.html", curr_res=list_res, num_curr_res = len(list_res))