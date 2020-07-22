from flask import render_template, request, redirect, url_for, current_app, flash
from flask_login import current_user, login_required
from datetime import datetime

from flask_app.app import scheduler
# import flask_app.src.sql_sqlalchemy as mydb
from flask_app.src.models import *
from flask_app.src.models.sql_query import get_fullListHosts, get_fullListResTypes, get_listCurrentReservations, get_listUsers, get_entryObject, get_idFromUsername
from flask_app.src.models.sql_insert import insert_newEntry
from flask_app.src.models.sql_update import update_configRestype
from flask_app.src.models.sql_delete import manual_removeReservation, timed_removeReservation, del_restype
from flask_app.src.models.aux_checks import check_conflictsNewReservation

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

    # get list of enabled hosts in the database
    list_hosts = get_fullListHosts(enabled=True, log_args=log_args)
    print(list_hosts)

    # get full list of reservation types in the database
    list_restypes = get_fullListResTypes(log_args=log_args)
    print(list_restypes)
    # print(list_restypes_ids)
    
    # list_freehosts = dbmain.get_listFreeHosts(log_args=log_args)
    # print(list_freehosts)
    list_freehosts = []

    # log_args = {"app": current_app, "user": current_user.username}

    # get list of current reservations (all users) in the database
    list_res = get_listCurrentReservations(log_args=log_args)
    print(list_res)

    print("YELLOW:'{}'".format(preselected_host))
    return render_template('layouts/reservations.html', presel_host=preselected_host, hosts=list_hosts, res_types=list_restypes, curr_res=list_res)

# Add new reservation page (POST only)
@app_routes.route('/new_reservation', methods=["POST"])
@login_required
def new_reservation():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    # get list of users in the database
    list_users = get_listUsers(log_args=log_args)
    username = request.form["username"]
    
    userID = get_idFromUsername(username)

    new_reservation = {}
    new_reservation["userID"] = userID
    # TODO: THIS CODE WAS REMOVED BECAUSE THIS SHOULD BE IMPOSSIBLE NOW WITH THE SINGLE DB, RECHECK IF IT WORKS
    # # check if user already exists in the database
    # if new_reservation["user"] not in list_users:
    #     # if not, needs to create user (this assumes the web app already authenticated the user)
    #     dbmain.insert_newUser(new_reservation["user"], log_args=log_args)
    #     # If web app is not authenticating user, it should return an error
    #     # return "ERROR: User '{}' does not exist!".format(new_reservation["user"])

    # Get the rest of the form fields
    new_reservation["hostID"] = request.form["host"]
    # new_reservation["host"] = request.form["host"]
    new_reservation["reservation_type"] = request.form["res_type"]
    datetimes = request.form["datetimes"]
    datetimes = datetimes.split(" - ")
    new_reservation["begin_date"] = datetimes[0]
    new_reservation["end_date"] = datetimes[1]

    # Check if end date is already past
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if new_reservation["end_date"] <= now:
        flash("ERROR: Reservation end date is already in the past ({})!".format(new_reservation["end_date"]))
        return redirect(url_for('app_routes.reservations', _external=True, _scheme='https'))
    
    # Checks for conflicts (Return True if there is a conflict)
    conflict, conflict_str = check_conflictsNewReservation(new_reservation, log_args)
    if not conflict:
        # Add reservation to DB
        new_res_obj = insert_newEntry(Reservation, new_reservation, log_args=log_args)
        if new_res_obj != -1:
            resID = new_res_obj.id

            # Create new trigger to end reservation at the end date
            scheduler.add_job(func=timed_removeReservation, trigger="date", run_date=new_reservation["end_date"], args=[resID], id='j'+str(resID), misfire_grace_time=7*24*60*60)
        else:
            flash("ERROR: Something went wrong.")
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

    resID = request.get_json().get("res_id", "")
    print(resID)

    # get database entry before removing
    res_obj = get_entryObject(Reservation, resID, log_args=log_args)
    print("ASDASDHASD")
    print(res_obj)

    # remove the entry from the db
    manual_removeReservation(res_obj, log_args)
    
    # TODO: Maybe flash green here?

    return "OK"


# Remove specific Reservation Type (POST only)
@app_routes.route('/remove_reservation_type', methods=["POST"])
@login_required
def remove_reservation_type():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    restypeID = request.get_json().get("res_id", "")
    
    del_restype(restypeID, log_args=log_args)

    return "OK"

# Update specific reservation type (change name or description) (POST only)
@app_routes.route('/update_reservation_type', methods=["POST"])
@login_required
def update_reservation_type():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    args = request.get_json()
    restypeID = args.get("id", "")
    name = args.get("name", "")
    description = args.get("description", "")

    update_configRestype(restypeID, name, description, log_args=log_args)

    return "OK"