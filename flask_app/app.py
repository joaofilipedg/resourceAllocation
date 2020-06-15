from flask import Flask, render_template, request, redirect, url_for
from flask_app.src import sql_connection as sql
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta

# from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder="templates/static")

@app.route('/')
@app.route('/login')
def hello_world():
    # return render_template('layouts/login.html')
    return redirect(url_for('reservations'))


@app.route('/reservations')
def reservations():
    list_hosts = sql.db_getListHosts()
    print(list_hosts)

    list_restypes, list_restypes_ids = sql.db_getListResTypes()
    print(list_restypes)
    print(list_restypes_ids)
    
    list_freehosts = sql.db_getFreeHosts()
    print(list_freehosts)

    list_res = sql.db_getCurrentReservations()
    print(list_res)
    return render_template('layouts/reservations.html', hosts=list_hosts, num_res_types=len(list_restypes), res_types=list_restypes, res_type_ids = list_restypes_ids, free_hosts=list_freehosts, curr_res=list_res)

@app.route('/new_reservation', methods=["POST"])
def new_reservation():
    # if request.method == "POST":



    list_users = sql.db_getListUsers()

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

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    # print(now)
    # print(new_reservation["end_date"] )
    # check if reservation enddate is already in the past
    if new_reservation["end_date"] <= now:
        return "RESERVATION END DATE IS ALREADY IN THE PAST ({})!".format(new_reservation["end_date"])

    
    res_id = sql.db_addNewReservation(new_reservation)

    # print
    # scheduler.add_job(func=sql.db_timedRemoveReservation, trigger="date", run_date=new_reservation["end_date"], args=[res_id, db], id='j'+str(res_id))
    scheduler.add_job(func=sql.db_timedRemoveReservation, trigger="date", run_date=new_reservation["end_date"], args=[res_id], id='j'+str(res_id))
    
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
    sql.db_removeReservation(res_id)
    return "OK"

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////mnt/c/Users/joaof/OneDrive/github/joaofilipedg/resourceAllocation/sqlite_db/res_alloc.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new_sqlalchemy_db.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db_alch = SQLAlchemy(app)

# class User(db_alch.Model):
#     id = db_alch.Column(db_alch.Integer, primary_key=True)
#     username = db_alch.Column(db_alch.String(80), unique=True, nullable=False)
#     email = db_alch.Column(db_alch.String(120), unique=True, nullable=False)
#     def __repr__(self):
#             return '<User %r>' % self.username

# def show_users():
#     with db_alch.app.app_context():
#         print(User.query.all())

def timed_func():
    print("5 seconds later")

# def sched_addNewRes(sched, new_reservation):
    


class Config(object):
    # JOBS = [
    #     {
    #         'id': 'job1',
    #         # 'func': show_users,
    #         'func': timed_func,
    #         'trigger': 'interval',    
    #         'replace_existing': True,
    #         'seconds': 5
    #     }
    # ]

    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:///flask_context.db')
    }

    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())
# db_alch.app = app
# db_alch.init_app(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    