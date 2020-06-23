import ldap
from flask import render_template, request, redirect, url_for, Blueprint, g, flash
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime

from flask_app.app import app, scheduler, dbmain, login_manager, dbldap
from flask_app.auth.models import User, LoginForm
import flask_app.src.sql_sqlalchemy as mydb

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@auth.before_request
def get_current_user():
    g.user = current_user

@auth.route('/')
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('auth.home'))

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            User.try_login(username, password)
        except ldap.INVALID_CREDENTIALS:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('layouts/login.html', form=form)

        user = User.query.filter_by(username=username).first()

        if not user:
            user = User(username)
            dbldap.session.add(user)
            dbldap.session.commit()

        login_user(user)
        # flash('You have successfully logged in.', 'success')

        return redirect(url_for('auth.home'))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('layouts/login.html', form=form)

@auth.route("/home")
@login_required
def home():
    username = current_user.username
    list_res = dbmain.get_listCurrentReservations(username)
    print(list_res)
    return render_template("layouts/home.html", curr_res=list_res)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Reservations page, to add new reservations, see current reservations or cancel one active reservation
@auth.route('/reservations')
@login_required
def reservations():
    list_hosts = dbmain.get_listHosts()
    print(list_hosts)

    list_restypes, list_restypes_ids = dbmain.get_listResTypes()
    print(list_restypes)
    print(list_restypes_ids)
    
    list_freehosts = dbmain.get_listFreeHosts()
    print(list_freehosts)

    list_res = dbmain.get_listCurrentReservations()
    print(list_res)
    return render_template('layouts/reservations.html', hosts=list_hosts, num_res_types=len(list_restypes), res_types=list_restypes, res_type_ids = list_restypes_ids, free_hosts=list_freehosts, curr_res=list_res)

# Add new reservation page (POST only)
@auth.route('/new_reservation', methods=["POST"])
@login_required
def new_reservation():

    list_users = dbmain.get_listUsers()
  
    new_reservation = {}
    new_reservation["user"] = request.form["username"]
    
    # check if user already exists in the database
    if new_reservation["user"] not in list_users:
        # if not, needs to create user (this assumes the web app already authenticated the user)
        dbmain.insert_newUser(new_reservation["user"])

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
    conflict, conflict_str = mydb.check_conflictsNewReservation(new_reservation)
    if not conflict:
        # Add reservation to DB
        res_id = dbmain.insert_newReservation(new_reservation)

        # Create new trigger to end reservation at the end date
        scheduler.add_job(func=mydb.timed_removeReservation, trigger="date", run_date=new_reservation["end_date"], args=[res_id], id='j'+str(res_id), misfire_grace_time=7*24*60*60)
    
        return redirect(url_for('auth.reservations'))
    else:
        return "ERROR: {}".format(conflict_str)
        
# Cancel reservation (POST only)
@auth.route('/cancel_reservation', methods=["POST"])
@login_required
def cancel_reservation():
    res_id = request.get_json().get("res_id", "")
    print(res_id)

    mydb.manual_removeReservation(res_id)
    return "OK"

# Edit page, to edit list of hosts, add new host,
@auth.route('/edit')
@login_required
def edit_db():
    full_list_hosts = dbmain.get_fullListHosts()
    print(full_list_hosts)

    # list_restypes, list_restypes_ids = dbmain.get_listResTypes()
    # print(list_restypes)
    # print(list_restypes_ids)

    return render_template('layouts/edit_db.html', hosts=full_list_hosts)

# Enable/Disable specific Host (POST only)
@auth.route('/toggle_host', methods=["POST"])
@login_required
def toggle_enable_host():
    hostname = request.get_json().get("hostname", "")
    print(hostname)

    dbmain.toggle_enableHost(hostname)
    return "OK"

# Remove specific Host (POST only)
@auth.route('/remove_host', methods=["POST"])
@login_required
def remove_host():
    hostname = request.get_json().get("hostname", "")
    print(hostname)

    dbmain.del_host(hostname)
    return "OK"

# Update specific Host (change IP address or GPU/FPGA availability) (POST only)
@auth.route('/update_host', methods=["POST"])
@login_required
def update_host():
    args = request.get_json()
    hostname = args.get("hostname", "")
    ipaddr = args.get("ip", "")
    gpu = args.get("gpu", "")
    fpga = args.get("fpga", "")

    dbmain.update_hostGPUFPGA(hostname, ipaddr, gpu, fpga)

    return "OK"

# Add new host page (POST only)
@auth.route('/new_host', methods=["POST"])
@login_required
def new_host():
    full_list_hosts = dbmain.get_fullListHosts()
    list_hostnames = [i[0] for i in full_list_hosts]
    list_ipaddrs = [i[1] for i in full_list_hosts]
    print(list_hostnames)
    print(list_ipaddrs)

    new_host = {}
    
    # check if hostname is already registered
    new_host["hostname"] = request.form["hostname"]
    if new_host["hostname"] in list_hostnames:
        return "ERROR: Host {} is already registered!".format(new_host["hostname"])

    
    # check if ipaddr is already in use
    new_host["ipaddr"] = request.form["ipaddr"]
    print(type(new_host["ipaddr"]))
    if int(new_host["ipaddr"]) in list_ipaddrs:
        return "ERROR: IP address X.X.X.{} is already being used!".format(new_host["ipaddr"])

    new_host["hasgpu"] = request.form["hasgpu"]
    new_host["hasfpga"] = request.form["hasfpga"]

    dbmain.insert_newHost(new_host)
    
    return redirect(url_for('auth.edit_db'))

