import sqlite3

def db_connect(path_to_db):
    db_conn = sqlite3.connect(path_to_db)
    return db_conn

def db_query(db, query):
    cursor = db.cursor()
    cursor.execute(query)
    return cursor.fetchall()

def db_getListHosts(db):
    query = "SELECT hostname FROM hosts ORDER BY hostname;"
    result_hosts = db_query(db, query)
    list_hosts = [i[0] for i in result_hosts]
    return list_hosts

def db_getListResTypes(db):
    query = "SELECT name, description FROM reservation_types;"
    results_restypes = db_query(db, query)
    list_restypes = [i[0] for i in results_restypes]
    return list_restypes

def db_getFreeHosts(db):
    query = "SELECT \
                hosts.hostname, \
                COUNT(res.host_id) as num_reservations \
            FROM \
                hosts \
                LEFT JOIN reservations as res ON hosts.id = res.host_id \
            GROUP BY hosts.id \
            HAVING num_reservations == 0 \
            ORDER BY hosts.hostname;"
    results = db_query(db, query)
    list_freehosts = [i[0] for i in results]
    return list_freehosts

def db_getCurrentReservations(db):
    query = "SELECT \
                hosts.hostname, \
                users.username, \
                res.reservation_type, \
                res.begin_date, \
                res.end_date \
            FROM \
                reservations as res \
                LEFT JOIN hosts ON hosts.id = res.host_id \
                LEFT JOIN users ON users.id = res.user_id \
            ORDER BY 1,2;"
    list_res = db_query(db, query)

    list_aux = []
    for res in list_res:
        list_aux_2 = []
        for val in res:
            list_aux_2.append(val)
        list_aux.append(list_aux_2)
    return list_aux