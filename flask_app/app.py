from flask import Flask, render_template, request, redirect, url_for
from flask_app.src import sql_connection as sql

app = Flask(__name__, static_folder="templates/static")

db = sql.db_connect("sqlite_db/res_alloc.db")

@app.route('/')
@app.route('/index')
def hello_world():
    # return render_template('layouts/index.html')
    return redirect(url_for('reservations'))


@app.route('/reservations')
def reservations():
    list_hosts = sql.db_getListHosts(db)
    print(list_hosts)

    list_restypes, list_restypes_ids = sql.db_getListResTypes(db)
    print(list_restypes)
    print(list_restypes_ids)
    
    list_freehosts = sql.db_getFreeHosts(db)
    print(list_freehosts)

    list_res = sql.db_getCurrentReservations(db)
    print(list_res)
    return render_template('layouts/reservations.html', hosts=list_hosts, num_res_types=len(list_restypes), res_types=list_restypes, res_type_ids = list_restypes_ids, free_hosts=list_freehosts, curr_res=list_res)

@app.route('/new_reservation', methods=["POST"])
def new_reservation():
    # if request.method == "POST":
    list_users = sql.db_getListUsers(db)

    new_reservation = {}
    new_reservation["user"] = request.form["username"]
    
    # check if user exists
    if new_reservation["user"] not in list_users:
        return "USER '{}' DOES NOT EXIST!".format(new_reservation["user"])

    new_reservation["host"] = request.form["host"]
    new_reservation["res_type"] = request.form["res_type"]
    datetimes = request.form["datetimes"]
    datetimes = datetimes.split(" - ")
    new_reservation["begin_date"] = datetimes[0]
    new_reservation["end_date"] = datetimes[1]

    sql.db_addNewReservation(db, new_reservation)
    
    return redirect(url_for('reservations'))

    
    # else:
    #     list_hosts = sql.db_getListHosts(db)
    #     print(list_hosts)

    #     list_restypes = sql.db_getListResTypes(db)
    #     print(list_restypes)
        
    #     list_freehosts = sql.db_getFreeHosts(db)
    #     print(list_freehosts)

    #     list_res = sql.db_getCurrentReservations(db)
    #     print(list_res)
    #     return render_template('layouts/reservations.html', hosts=list_hosts, res_types=list_restypes, free_hosts=list_freehosts, curr_res=list_res)

@app.route('/cancel_reservation', methods=["POST"])
def cancel_reservation():
    # print(request.get_json())
    res_id = request.get_json().get("res_id", "")
    print(res_id)
    sql.db_removeReservation(db, res_id)
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    