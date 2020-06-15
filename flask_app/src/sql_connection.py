import sqlite3

class ReservationsDB:
    def __init__(self, path_to_db):
        self.conn = sqlite3.connect(path_to_db)
        self.create_users_table()
        self.create_hosts_table()
        self.create_restypes_table()
        self.create_reservations_table()

    def create_users_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS "users" (
            username TEXT PRIMARY KEY NOT NULL
        );
        """
        self.conn.execute(query)
    
    def create_hosts_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS "hosts" (
            hostname TEXT PRIMARY KEY NOT NULL,
            has_gpu INTEGER NOT NULL,
            has_fpga INTEGER NOT NULL
            );
        """
        self.conn.execute(query)

    def create_restypes_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS "reservation_types" (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT
            );
        """
        self.conn.execute(query)

    def create_reservations_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS "reservations" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            host TEXT NOT NULL,
            reservation_type INTEGER NOT NULL,
            begin_date TEXT,
            end_date TEXT,
            FOREIGN KEY (user) REFERENCES users(username),
            FOREIGN KEY (host) REFERENCES hosts(hostname),
            FOREIGN KEY (reservation_type) REFERENCES reservation_types(id)
            );
        """
        self.conn.execute(query)


# # Connect to a sqlite database
# def db_connect(path_to_db):
#     return ReservationsDB(path_to_db)

db = ReservationsDB("sqlite_db/res_alloc.db")

# Query the database
def db_query(query):
    cursor = db.conn.cursor()
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
    cursor =  db.conn.cursor()
    cursor.execute(insert)
    # print(cursor.lastrowid)
    db.conn.commit()

    return cursor.lastrowid

def db_removeReservation(res_id):
    delete = "DELETE FROM reservations WHERE id={}".format(res_id)
    
    print(delete)
    cursor = db.conn.cursor()
    cursor.execute(delete)
    db.conn.commit()

    return True

def db_timedRemoveReservation(*args):
    res_id = args[0]
    print("Time's up! Finishing reservation with id {}".format(res_id))
    db_temp = ReservationsDB("sqlite_db/res_alloc.db")

    delete = "DELETE FROM reservations WHERE id={}".format(res_id)
    print(delete)
    cursor = db_temp.conn.cursor()
    cursor.execute(delete)
    db_temp.conn.commit()
    return True