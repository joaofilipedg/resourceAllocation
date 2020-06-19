from flask import Flask, render_template, request, redirect, url_for
from flask_app.src import sql_sqlalchemy as mydb
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_apscheduler import APScheduler
from datetime import datetime

# from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder="templates/static")


# MAIN PAGE - Login
@app.route('/')
@app.route('/login')
def hello_world():
    return render_template('layouts/login.html')
    # return redirect(url_for('reservations'))

# Reservations page, to add new reservations, see current reservations or cancel one active reservation
@app.route('/reservations')
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
@app.route('/new_reservation', methods=["POST"])
def new_reservation():
    # if request.method == "POST":

    list_users = dbmain.get_listUsers()

    new_reservation = {}
    new_reservation["user"] = request.form["username"]
    
    # check if user exists
    if new_reservation["user"] not in list_users:
        return "ERROR: User '{}' does not exist!".format(new_reservation["user"])

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
        scheduler.add_job(func=mydb.timed_removeReservation, trigger="date", run_date=new_reservation["end_date"], args=[res_id], id='j'+str(res_id), misfire_grace_time=24*60*60)
    
        return redirect(url_for('reservations'))
    else:
        return "ERROR: {}".format(conflict_str)
# Cancel reservation (POST only)
@app.route('/cancel_reservation', methods=["POST"])
def cancel_reservation():
    res_id = request.get_json().get("res_id", "")
    print(res_id)

    mydb.manual_removeReservation(res_id)
    return "OK"

# Edit page, to edit list of hosts, add new host,
@app.route('/edit')
def edit_db():
    full_list_hosts = dbmain.get_fullListHosts()
    print(full_list_hosts)

    # list_restypes, list_restypes_ids = dbmain.get_listResTypes()
    # print(list_restypes)
    # print(list_restypes_ids)

    return render_template('layouts/edit_db.html', hosts=full_list_hosts)

# Enable/Disable specific Host (POST only)
@app.route('/toggle_host', methods=["POST"])
def toggle_enable_host():
    hostname = request.get_json().get("hostname", "")
    print(hostname)

    dbmain.toggle_enableHost(hostname)
    return "OK"

# Remove specific Host (POST only)
@app.route('/remove_host', methods=["POST"])
def remove_host():
    hostname = request.get_json().get("hostname", "")
    print(hostname)

    dbmain.del_host(hostname)
    return "OK"

# Update specific Host (change IP address or GPU/FPGA availability) (POST only)
@app.route('/update_host', methods=["POST"])
def update_host():
    args = request.get_json()
    hostname = args.get("hostname", "")
    ipaddr = args.get("ip", "")
    gpu = args.get("gpu", "")
    fpga = args.get("fpga", "")

    dbmain.update_hostGPUFPGA(hostname, ipaddr, gpu, fpga)

    return "OK"

# Add new host page (POST only)
@app.route('/new_host', methods=["POST"])
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
    
    return redirect(url_for('edit_db'))


class Config(object):
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:///sqlite_db/flask_scheduler_context.db')
    }

    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

dbmain = mydb.ReservationsDB(mydb.SQLITE, dbname="sqlite_db/res_alloc2.db")

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    