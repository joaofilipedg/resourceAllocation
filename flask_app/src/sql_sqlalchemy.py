from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from flask_app.src.functions import read_csv

# Global Variables
SQLITE          = 'sqlite'

# Table Names
USERS           = 'users'
HOSTS           = 'hosts'
RESTYPES        = 'reservation_types'
RESERVATIONS    = 'reservations'


INSERT_INTO = "INSERT INTO {} VALUES {};"
RESERVATIONS_TABLE = "reservations(user, host, reservation_type, begin_date, end_date)"

# SQLALCHEMY DB
class ReservationsDB:
    # http://docs.sqlalchemy.org/en/latest/core/engines.html
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}',
    }

    # Main DB Connection Ref Obj
    db_engine = None

    # Creates Database
    def __init__(self, dbtype, username='', password='', dbname=''):
        dbtype = dbtype.lower()

        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)

            self.db_engine = create_engine(engine_url)
            print(self.db_engine)
            
            # Only adds the tables and fills them with data if it was non-existent
            TABLES_MISSING = []
            for table in [USERS, HOSTS, RESTYPES, RESERVATIONS]:
                if not self.db_engine.dialect.has_table(self.db_engine, table): 
                    print("Missing Table {}.".format(table))
                    TABLES_MISSING.append(table)

            if len(TABLES_MISSING) > 0:
                self.create_db_tables(TABLES_MISSING)
                self.fill_defaults(TABLES_MISSING)
        else:
            print("DBType is not found in DB_ENGINE")

    # Function to create the tables in the DB
    def create_db_tables(self, TABLES_MISSING):
        metadata = MetaData()

        if USERS in TABLES_MISSING:
            users = Table(USERS, metadata,
                            Column('username', String, primary_key=True, nullable=False)
                            )

        if HOSTS in TABLES_MISSING:
            hosts = Table(HOSTS, metadata,
                        Column('hostname', String, primary_key=True, nullable=False),
                        Column('has_gpu', Integer, nullable=False),
                        Column('has_fpga', Integer, nullable=False),
                        Column('enabled', Integer, nullable=False)
                        )

        if RESTYPES in TABLES_MISSING:
            restypes = Table(RESTYPES, metadata,
                        Column('id', Integer, primary_key=True, nullable=False),
                        Column('name', String),
                        Column('description', String)
                        )

        if RESERVATIONS in TABLES_MISSING:
            reservations = Table(RESERVATIONS, metadata,
                            Column('id', Integer, primary_key=True, autoincrement="auto"),
                            Column('user', String, ForeignKey('users.username'), nullable=False),
                            Column('host', String, ForeignKey('hosts.hostname'), nullable=False),
                            Column('reservation_type', Integer, ForeignKey('reservation_types.id'), nullable=False),
                            Column('begin_date', String),
                            Column('end_date', String)
                            )

        try:
            metadata.create_all(self.db_engine, checkfirst=True)
            print("Tables created")
        except Exception as e:
            print("Error occurred during Table creation!")
            print(e)

    # Fill missing tables with default values
    def fill_defaults(self, TABLES_MISSING):
            for table in TABLES_MISSING:
                if table != RESERVATIONS:
                    def_file = read_csv("sqlite_db/defaults/def_{}.csv".format(table), ";")
                    print(def_file)
                    for row in def_file:
                        if len(row) == 1:
                            values = "\"" + row[0] + "\""
                        else:
                            if table == HOSTS:
                                values = "\"" + row[0] + "\""

                                # checks if each host has GPU or FPGA
                                for value in row[1:]:
                                    if "has" in value:
                                        values += ", 1"
                                    else:
                                        values += ", 0"
                                
                                #make all hosts enabled by default
                                values += ", 1"
                            else:
                                values = row[0]
                                for value in row[1:]:
                                    values += ", '{}'".format(value)

                        self.insert(table, "({})".format(values))

    # Insert, Update, Delete
    def execute_query(self, query=''):
        if query == '': 
            return -1

        print(query)
        with self.db_engine.connect() as connection:
            try:
                result = connection.execute(query)
                return result.lastrowid
            except Exception as e:
                print(e)
                return -1

    def print_query(self, table='', query='', num_cols=-1):
        query = query if query != '' else "SELECT * FROM '{}';".format(table)
        print(query)
        out = []
        with self.db_engine.connect() as connection:
            try:
                result = connection.execute(query)
            except Exception as e:
                print(e)
            else:
                if (num_cols == 1) or (len(result.keys()) == 1):
                    out = [i[0] for i in result]
                else:
                    # out = [j for i in result for j in i]
                    out = []
                    for row in result:
                        list_aux = []
                        for val in row:
                            list_aux.append(val)
                        out.append(list_aux)
                # print(out)
                result.close()
        return out

    def insert(self, table, values):
        # Insert Data
        query = "INSERT INTO {} " \
                " VALUES {};".format(table, values)
        self.execute_query(query)

    def insert_newReservation(self, new_res):
        new_res_str = "(\"{}\", \"{}\", {}, \"{}\", \"{}\")".format(new_res["user"], new_res["host"], new_res["res_type"], new_res["begin_date"], new_res["end_date"])
        insert = INSERT_INTO.format(RESERVATIONS_TABLE, new_res_str)
        
        lastrowid = self.execute_query(insert)

        return lastrowid

    def del_entry(self, table, column, value):
        delete = "DELETE FROM {} WHERE {}={};".format(table, column, value)
        self.execute_query(delete)
        return True

    # def del_reservation(self, res_id):
    #     return self.del_entry(RESERVATIONS, res_id)

    def del_host(self, hostname):
        return self.del_entry(HOSTS, "hostname", "\""+hostname+"\"")

    def toggle_enableHost(self, hostname):
        query = "SELECT enabled FROM {} WHERE hostname=\"{}\";".format(HOSTS, hostname)
        enabled = self.print_query(query=query)[0]
        print(enabled)
        enabled = 1 - enabled
        update = "UPDATE {} SET enabled = {} WHERE hostname=\"{}\"".format(HOSTS, enabled, hostname)
        self.execute_query(update)
        return True

    # def del_timedReservation(self, res_id):
    #     print("Time's up! Finishing reservation with id {}".format(res_id))
    #     return self.del_reservation(res_id)


    # QUERIES
    def get_listUsers(self):
        query = "SELECT username FROM users ORDER BY username;"
        return self.print_query(query=query)
    
    def get_listHosts(self):
        # query = "SELECT hostname FROM hosts ORDER BY hostname;"
        query = "SELECT hostname FROM hosts WHERE enabled=1 ORDER BY hostname;"
        return self.print_query(query=query)

    def get_listResTypes(self):
        query = "SELECT name, id, description FROM reservation_types;"
        
        result_query = self.print_query(query=query)

        print(result_query)
        list_restypes = [i[0] for i in result_query]
        list_restypes_ids = [i[1] for i in result_query]

        # return result_query
        return list_restypes, list_restypes_ids

    def get_fullListHosts(self):
        query = "SELECT * FROM hosts ORDER BY hostname;"
        return self.print_query(query=query)


    def get_listFreeHosts(self):
        query = "SELECT \
                hosts.hostname, \
                COUNT(res.host) as num_reservations \
            FROM \
                hosts \
                LEFT JOIN reservations as res ON hosts.hostname = res.host \
            WHERE hosts.enabled = 1 \
            GROUP BY hosts.hostname \
            HAVING num_reservations == 0 \
            ORDER BY hosts.hostname;"
        return self.print_query(query=query, num_cols=1)
   
    def get_listCurrentReservations(self):
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
        return self.print_query(query=query)


# Function activated by the scheduler when END Time of a reservation activates
def timed_removeReservation(*args):
    from flask_app.app import dbmain
    res_id = args[0]
    
    print("Time's up! Finishing reservation with id {}".format(res_id))
    return dbmain.del_entry(RESERVATIONS, "id", res_id)

# Function activated when user manually cancels reservation    
def manual_removeReservation(res_id):
    from flask_app.app import dbmain, scheduler

    # must also remove scheduled remove action from the scheduler
    scheduler.remove_job(id='j'+str(res_id))
    
    return dbmain.del_entry(RESERVATIONS, "id", res_id)
