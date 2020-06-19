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
                        Column('ip', Integer, nullable=False),
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
                                
                                # row format: hostname, ip, has_gpu, has_fpga
                                values = "\"" + row[0] + "\"" + ', ' + row[1]

                                # checks if each host has GPU or FPGA
                                for value in row[2:]:
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
        query = "INSERT INTO {} VALUES {};".format(table, values)
        return self.execute_query(query)

    def insert_newReservation(self, new_res):
        new_res_str = "(\"{user}\", \"{host}\", {restype}, \"{begin}\", \"{end}\")"\
            .format(user=new_res["user"], host=new_res["host"], restype=new_res["res_type"], begin=new_res["begin_date"], end=new_res["end_date"])

        return self.insert(RESERVATIONS_TABLE, new_res_str)

    def insert_newHost(self, new_host):
        new_host_str = "(\"{host}\", {ip}, {gpu}, {fpga}, 1)".format(host=new_host["hostname"], \
            ip=new_host["ipaddr"], gpu=1 if new_host["hasgpu"]=="Yes" else 0, fpga=1 if new_host["hasfpga"]=="Yes" else 0)

        return self.insert(HOSTS, new_host_str)

    def del_entry(self, table, column, value):
        delete = "DELETE FROM {} WHERE {}={};".format(table, column, value)
        self.execute_query(delete)
        return True

    # Remove host from database
    def del_host(self, hostname):
        
        # Before removing host, remove all reservations associated with it
        list_res = self.get_listReservationsHost(hostname, "id")
        for res_id in list_res:
            manual_removeReservation(res_id)

        return self.del_entry(HOSTS, "hostname", "\""+hostname+"\"")

    def toggle_enableHost(self, hostname):
        query = "SELECT enabled FROM {} WHERE hostname=\"{}\";".format(HOSTS, hostname)
        enabled = self.print_query(query=query)[0]
        print(enabled)
        enabled = 1 - enabled
        update = "UPDATE {} SET enabled = {} WHERE hostname=\"{}\"".format(HOSTS, enabled, hostname)
        self.execute_query(update)
        return True

    def update_hostGPUFPGA(self, hostname, ipaddr, has_gpu, has_fpga):
        int_has_gpu = 1 if has_gpu == "Yes" else 0
        int_has_fpga = 1 if has_fpga == "Yes" else 0

        update = "UPDATE {} SET ip = {} WHERE hostname=\"{}\"".format(HOSTS, ipaddr, hostname)
        self.execute_query(update)

        update = "UPDATE {} SET has_gpu = {} WHERE hostname=\"{}\"".format(HOSTS, int_has_gpu, hostname)
        self.execute_query(update)

        update = "UPDATE {} SET has_fpga = {} WHERE hostname=\"{}\"".format(HOSTS, int_has_fpga, hostname)
        self.execute_query(update)
        return True


    # QUERIES
    def get_listUsers(self):
        query = "SELECT username FROM {users} ORDER BY username;".format(users=USERS)
        return self.print_query(query=query)
    
    def get_listHosts(self):
        # query = "SELECT hostname FROM hosts ORDER BY hostname;"
        query = "SELECT hostname FROM {hosts} WHERE enabled=1 ORDER BY hostname;".format(hosts=HOSTS)
        return self.print_query(query=query)

    def get_listResTypes(self):
        query = "SELECT name, id, description FROM {restypes};".format(restypes=RESTYPES)
        
        result_query = self.print_query(query=query)

        print(result_query)
        list_restypes = [i[0] for i in result_query]
        list_restypes_ids = [i[1] for i in result_query]

        # return result_query
        return list_restypes, list_restypes_ids

    # Get full list of all hosts (including hasgpu, hasfpga and enabled fields)
    def get_fullListHosts(self):
        query = "SELECT * FROM {hosts} ORDER BY hostname;".format(hosts=HOSTS)
        return self.print_query(query=query)


    # Get list of current free hosts (that are enabled)
    def get_listFreeHosts(self):
        query = "SELECT \
                    {hosts}.hostname, \
                    COUNT(res.host) as num_reservations \
                FROM \
                    {hosts} \
                    LEFT JOIN {res} as res ON {hosts}.hostname = res.host \
                WHERE {hosts}.enabled = 1 \
                GROUP BY {hosts}.hostname \
                HAVING num_reservations == 0 \
                ORDER BY {hosts}.hostname;".format(res=RESERVATIONS, hosts=HOSTS)
        return self.print_query(query=query, num_cols=1)
   
    # Get list of all current scheduled reservations 
    def get_listCurrentReservations(self, hostname=""):
        query = "SELECT \
                    {hosts}.hostname, \
                    {users}.username, \
                    res_t.name, \
                    res.begin_date, \
                    res.end_date, \
                    res.id \
                FROM \
                    {res} as res \
                    LEFT JOIN {hosts} ON {hosts}.hostname = res.host \
                    LEFT JOIN {users} ON {users}.username = res.user \
                    LEFT JOIN {restypes} as res_t ON res_t.id = res.reservation_type \
                ORDER BY 1,2;".format(res=RESERVATIONS, hosts=HOSTS, users=USERS, restypes=RESTYPES)
        return self.print_query(query=query)

    def get_listReservationsHost(self, hostname, column):
        query = "SELECT {col} \
                FROM {res} \
                WHERE host=\"{host}\";".format(res=RESERVATIONS, col=column, host=hostname)
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

# Function to check if a new reservation conflicts with any of the previous ones
# (Return True if there is a conflict)
def check_conflictsNewReservation(new_res):
    from flask_app.app import dbmain
    
    list_res = dbmain.get_listReservationsHost(new_res["host"], "*")
    
    idx_begin_date = 4
    idx_end_date = idx_begin_date+1
    idx_restype = 3
    for res in list_res:
        # Check if there is any intersection of the timeslot
        if (new_res["end_date"] <= res[idx_begin_date]) or (new_res["begin_date"] >= res[idx_end_date]):
            continue
        else:
            # if there is, need to check if the reservation types results in conflicts or not

            # Uncomment to debug
            # print("\tPossible conflict (Time is conflicting with res {})".format(res[0]))
            # print("\tres: '{}'".format(res))
            # print("\tnew_res: '{}'".format(new_res))
            # print("\t\tres[res_type]: '{}'".format(res[idx_restype]))
            # print("\t\tnew_res[res_type]: '{}'".format(new_res["res_type"]))

            # if either of the reservations (old conflicting one or new one) is of type 1 (RESERVED FULL)
            conflict_res = "<br/><br/>Conflicting reservation (id, username, hostname, reservation_type, begin_date, end_date):<br/>    {}".format(res)
            if (res[idx_restype] == 1) or (int(new_res["res_type"]) == 1):
                error_str = "New reservation conflicts with existing reservation. (One of them is of type 'RESERVED FULL SYSTEM')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res
            
            # if both reservations (old conflicting one and new one) are locking the FPGA (RESERVED FPGA)
            if (res[idx_restype] == 2) and (int(new_res["res_type"]) == 2):
                error_str = "New reservation conflicts with existing reservation. (Both of them are of type 'RESERVED FPGA')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res
            
            # if both reservations (old conflicting one and new one) are locking the GPU (RESERVED GPU)
            if (res[idx_restype] == 3) and (int(new_res["res_type"]) == 3):
                error_str = "New reservation conflicts with existing reservation. (Both of them are of type 'RESERVED GPU')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res

            # if old res is RESERVED_GPU or RESERVED_FPGA and new one is DEVELOPING or RUNNING PROGRAMS
            if ((res[idx_restype] == 2) or (res[idx_restype] == 3)) and ((int(new_res["res_type"]) == 4) or (int(new_res["res_type"]) == 5)):
                error_str = "New reservation conflicts with existing reservation. (New reservation is of type 'DEVELOPING' or 'RUNNING PROGRAMS/SIMULATIONS', which conflicts with reservations of type 'RESERVED FPGA' or 'RESERVED GPU')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res

            # if old res is DEVELOPING or RUNNING PROGRAMS and new one is RESERVED_GPU or RESERVED_FPGA 
            if ((res[idx_restype] == 4) or (res[idx_restype] == 5)) and ((int(new_res["res_type"]) == 2) or (int(new_res["res_type"]) == 3)):
                error_str = "New reservation conflicts with existing reservation. (Existing reservation is of type 'DEVELOPING' or 'RUNNING PROGRAMS/SIMULATIONS', which conflicts with new reservation of type 'RESERVED FPGA' or 'RESERVED GPU')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res
            # if 

    return False, ""
