import sqlite3


# Connect to a sqlite database
def db_connect(path_to_db):
    db_conn = sqlite3.connect(path_to_db)
    return db_conn

db = db_connect("sqlite_db/res_alloc.db")

# Query the database
def db_query(query):
    cursor = db.cursor()
    cursor.execute(query)
    return cursor.fetchall()


def db_queryFirstColumn(query):
    result = db_query(query)
    list_values = [i[0] for i in result]
    return list_values

# Convert the query results output into a list
def db_listFromQuery(query):
    result = db_query(query)
    list_values = [i[0] for i in result]
    list_ids = [i[1] for i in result]
    return list_values, list_ids

# Get list of users
def db_getListUsers():
    query = "SELECT username FROM users ORDER BY username;"
    return db_queryFirstColumn(query)

# Get list of hosts
def db_getListHosts():
    query = "SELECT hostname FROM hosts ORDER BY hostname;"
    return db_queryFirstColumn(query)

# Get list of possible reservation types
def db_getListResTypes():
    query = "SELECT name, id, description FROM reservation_types;"
    return db_listFromQuery(query)

# Get list of free hosts
def db_getFreeHosts():
    query = "SELECT \
                hosts.hostname, \
                COUNT(res.host) as num_reservations \
            FROM \
                hosts \
                LEFT JOIN reservations as res ON hosts.hostname = res.host \
            GROUP BY hosts.hostname \
            HAVING num_reservations == 0 \
            ORDER BY hosts.hostname;"
    return db_queryFirstColumn(query)

# Get list of current reservations
def db_getCurrentReservations():
    query = "SELECT \
                hosts.hostname, \
                users.username, \
                res_t.name, \
                res.begin_date, \
                res.end_date, \
                res.id \
            FROM \
                reservations as res \
                LEFT JOIN hosts ON hosts.hostname = res.host \
                LEFT JOIN users ON users.username = res.user \
                LEFT JOIN reservation_types as res_t ON res_t.id = res.reservation_type \
            ORDER BY 1,2;"
    list_res = db_query(query)

    list_aux = []
    for res in list_res:
        list_aux_2 = []
        for val in res:
            list_aux_2.append(val)
        list_aux.append(list_aux_2)
    return list_aux

INSERT_INTO = "INSERT INTO {} VALUES {};"
RESERVATIONS_TABLE = "reservations(user, host, reservation_type, begin_date, end_date)"
def db_addNewReservation(new_res):
    new_res_str = "(\"{}\", \"{}\", {}, \"{}\", \"{}\")".format(new_res["user"], new_res["host"], new_res["res_type"], new_res["begin_date"], new_res["end_date"])
    insert = INSERT_INTO.format(RESERVATIONS_TABLE, new_res_str)
    
    print(insert)
    cursor = db.cursor()
    cursor.execute(insert)
    # print(cursor.lastrowid)
    db.commit()

    return cursor.lastrowid

def db_removeReservation(res_id):
    delete = "DELETE FROM reservations WHERE id={}".format(res_id)
    
    print(delete)
    cursor = db.cursor()
    cursor.execute(delete)
    db.commit()

    return True

def db_timedRemoveReservation(*args):
    res_id = args[0]
    print("Time's up! Finishing reservation with id {}".format(res_id))
    db_temp = db_connect("sqlite_db/res_alloc.db")

    delete = "DELETE FROM reservations WHERE id={}".format(res_id)
    print(delete)
    cursor = db_temp.cursor()
    cursor.execute(delete)
    db_temp.commit()
    return True