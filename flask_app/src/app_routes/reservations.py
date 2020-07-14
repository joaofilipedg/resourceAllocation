from flask import render_template, request, redirect, url_for, current_app, flash
from flask_login import current_user, login_required
from datetime import datetime

from flask_app.app import scheduler
import flask_app.src.sql_sqlalchemy as mydb
from flask_app.src.sql_sqlalchemy import dbmain

from . import app_routes

# Reservations page, to add new reservations, see current reservations or cancel one active reservation
@app_routes.route('/reservations', methods=['GET', 'POST'])
@login_required
def reservations():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    preselected_host = "nothing"
    if request.method == 'POST':
        print(request.form)
        preselected_host = request.form["host"]

    list_hosts = dbmain.get_listEnabledHosts(log_args=log_args)
    print(list_hosts)

    list_restypes, list_restypes_ids = dbmain.get_listResTypes(log_args=log_args)
    print(list_restypes)
    print(list_restypes_ids)
    
    list_freehosts = dbmain.get_listFreeHosts(log_args=log_args)
    print(list_freehosts)

    log_args = {"app": current_app, "user": current_user.username}

    list_res = dbmain.get_listCurrentReservations(log_args=log_args)
    print(list_res)

    print("YELLOW:'{}'".format(preselected_host))
    return render_template('layouts/reservations.html', presel_host=preselected_host, hosts=list_hosts, num_res_types=len(list_restypes), res_types=list_restypes, res_type_ids = list_restypes_ids, free_hosts=list_freehosts, curr_res=list_res)

# Add new reservation page (POST only)
@app_routes.route('/new_reservation', methods=["POST"])
@login_required
def new_reservation():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    list_users = dbmain.get_listUsers(log_args=log_args)
  
    new_reservation = {}
    new_reservation["user"] = request.form["username"]
    
    # check if user already exists in the database
    if new_reservation["user"] not in list_users:
        # if not, needs to create user (this assumes the web app already authenticated the user)
        dbmain.insert_newUser(new_reservation["user"], log_args=log_args)

        # If web app is not authenticating user, it should return an error
        # return "ERROR: User '{}' does not exist!".format(new_reservation["user"])

    # Get the rest of the form fields
    new_reservation["host"] = request.form["host"]
    new_reservation["res_type"] = request.form["res_type"]
    datetimes = request.form["datetimes"]
    datetimes = datetimes.split(" - ")
    new_reservation["begin_date"] = datetimes[0]
    new_reservation["end_date"] = datetimes[1]

    # Check if end date is already past
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if new_reservation["end_date"] <= now:
        return "ERROR: Reservation end date is already in the past ({})!".format(new_reservation["end_date"])

    # Checks for conflicts (Return True if there is a conflict)
    conflict, conflict_str = mydb.check_conflictsNewReservation(new_reservation, log_args)
    if not conflict:
        # Add reservation to DB
        res_id = dbmain.insert_newReservation(new_reservation, log_args=log_args)

        # Create new trigger to end reservation at the end date
        scheduler.add_job(func=mydb.timed_removeReservation, trigger="date", run_date=new_reservation["end_date"], args=[res_id], id='j'+str(res_id), misfire_grace_time=7*24*60*60)
    
    else:
        flash("ERROR: {}".format(conflict_str))
    return redirect(url_for('app_routes.reservations', _external=True, _scheme='https'))
        # return redirect(url_for('app_routes.reservations', _external=True, _scheme='https'))
        # return "ERROR: {}".format(conflict_str)
        
# Cancel reservation (POST only)
@app_routes.route('/cancel_reservation', methods=["POST"])
@login_required
def cancel_reservation():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    res_id = request.get_json().get("res_id", "")
    print(res_id)

    mydb.manual_removeReservation(res_id, log_args)
    return "OK"
