from flask import Flask, render_template
from flask_app.src import sql_connection as sql

app = Flask(__name__, static_folder="templates/static")

db = sql.db_connect("sqlite_db/res_alloc.db")

@app.route('/')
def hello_world():
    return render_template('layouts/index.html')


@app.route('/reservations')
def reservations():
    list_hosts = sql.db_getListHosts(db)
    print(list_hosts)

    list_restypes = sql.db_getListResTypes(db)
    print(list_restypes)
    
    list_freehosts = sql.db_getFreeHosts(db)
    print(list_freehosts)

    list_res = sql.db_getCurrentReservations(db)
    print(list_res)
    return render_template('layouts/reservations.html', hosts=list_hosts, res_types=list_restypes, free_hosts=list_freehosts, curr_res=list_res)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0')
    