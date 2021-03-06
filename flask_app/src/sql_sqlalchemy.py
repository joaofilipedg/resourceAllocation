import sys
import logging
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, select, func, join, alias, exists
from sqlalchemy_utils import create_view

from flask_app.src.global_stuff import read_csv, DEBUG_MODE

# Global Variables
SQLITE          = 'sqlite'

# Table Names
USERS           = 'users'
COMPONENTS      = 'components'
HOSTS           = 'hosts'
HOSTSCOMPONENTS = 'hostscomponents'
RESTYPES        = 'reservation_types'
RESERVATIONS    = 'reservations'

# Views Names
HOSTS_FULL      = "hosts_full"
HOSTSCOMPS_FULL = "hostscomps_full"


ALL_TABLES      = [USERS, COMPONENTS, HOSTS, HOSTSCOMPONENTS, RESTYPES, RESERVATIONS]
ALL_VIEWS       = [HOSTS_FULL, HOSTSCOMPS_FULL]

# Components type coders
CODE_CPU        = 0
CODE_GPU        = 1
CODE_FPGA       = 2

# Table Schemas
COMPONENTS_SCHEMA= "{}(type, name, generation, manufacturer)".format(COMPONENTS)
HOSTS_SCHEMA= "{}(hostname, ip, enabled)".format(HOSTS)
RESERVATIONS_SCHEMA = "{}(user, host, reservation_type, begin_date, end_date)".format(RESERVATIONS)

INSERT_INTO = "INSERT INTO {} VALUES {};"

# IN RESERVATION TABLES
IDX_BEGIN_DATE = 4
IDX_END_DATE = IDX_BEGIN_DATE+1
IDX_RESTYPE = 3


SQLITE_LEVEL_NUM = 25
if not DEBUG_MODE:
    # Create custom logging level for SQLITE accesses
    logging.addLevelName(SQLITE_LEVEL_NUM, "SQLITE")
    def infosql(self, message, *args, **kws):
        if self.isEnabledFor(SQLITE_LEVEL_NUM):
            self._log(SQLITE_LEVEL_NUM, message, args, **kws) 
    logging.Logger.infosql = infosql


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
            for table in ALL_TABLES:
                if not self.db_engine.dialect.has_table(self.db_engine, table): 
                    print("Missing Table {}.".format(table))
                    TABLES_MISSING.append(table)

            if len(TABLES_MISSING) > 0:
                self.create_db_tables(TABLES_MISSING)
                self.fill_defaults(TABLES_MISSING)

            VIEWS_MISSING = []
            list_views = self.db_engine.dialect.get_view_names(self.db_engine)
            for view in ALL_VIEWS:
                if view not in list_views:
                    VIEWS_MISSING.append(view)
            
            if len(VIEWS_MISSING) > 0:
                self.create_db_views(VIEWS_MISSING)
        else:
            print("DBType is not found in DB_ENGINE")

    # Function to create the tables in the DB
    def create_db_tables(self, TABLES_MISSING):
        metadata = MetaData()

        if USERS in TABLES_MISSING:
            print("Adding Table {}".format(USERS))
            users = Table(USERS, metadata,
                            Column('username', String, primary_key=True, nullable=False)
                            )

        if COMPONENTS in TABLES_MISSING:
            print("Adding Table {}".format(COMPONENTS))
            components = Table(COMPONENTS, metadata,
                            Column('componentID', Integer, primary_key=True, autoincrement="auto"),
                            Column('type', Integer), # component.type: 0-CPU; 1-GPU; 2-FPGA
                            Column('name', String), # component/device name
                            Column('generation', String), # device family (eg., Haswell (cpu), Skylake (cpu), Volta (gpu), etc)
                            Column('manufacturer', String) # Manufacturer (eg., Intel, AMD, NVIDIA, Xilinx, etc.)
                            )
                            
        if HOSTS in TABLES_MISSING:
            print("Adding Table {}".format(HOSTS))
            hosts = Table(HOSTS, metadata,
                        Column('hostname', String, primary_key=True, nullable=False),
                        Column('ip', Integer, nullable=False),
                        Column('enabled', Integer, nullable=False),
                        Column('cpu', Integer, ForeignKey('{components}.componentID'.format(components=COMPONENTS)))
                        )

        if HOSTSCOMPONENTS in TABLES_MISSING:
            print("Adding Table {}".format(HOSTSCOMPONENTS))
            # n-m relation table
            hostscomponents = Table("hostscomponents", metadata,
                                Column("hostname", String, ForeignKey('{hosts}.hostname'.format(hosts=HOSTS)), primary_key=True, nullable=False),
                                Column("componentID", Integer, ForeignKey('{components}.componentID'.format(components=COMPONENTS)), primary_key=True, nullable=False)
                                )

        if RESTYPES in TABLES_MISSING:
            print("Adding Table {}".format(RESTYPES))
            restypes = Table(RESTYPES, metadata,
                        Column('restypeID', Integer, primary_key=True, nullable=False),
                        Column('name', String),
                        Column('description', String)
                        )

        if RESERVATIONS in TABLES_MISSING:
            print("Adding Table {}".format(RESERVATIONS))
            reservations = Table(RESERVATIONS, metadata,
                            Column('reservationID', Integer, primary_key=True, autoincrement="auto"),
                            Column('user', String, ForeignKey('{users}.username'.format(users=USERS)), nullable=False),
                            Column('host', String, ForeignKey('{hosts}.hostname'.format(hosts=HOSTS)), nullable=False),
                            Column('reservation_type', Integer, ForeignKey('reservation_types.restypeID'), nullable=False),
                            Column('begin_date', String),
                            Column('end_date', String)
                            )

        try:
            metadata.create_all(self.db_engine, checkfirst=True)
            print("Tables created")
        except Exception as e:
            print("Error occurred during Table creation!")
            if not DEBUG_MODE:
                logging.critical("Error occurred during Table creation!", exc_info=True)
            print(e)

    # Function to create the views in the DB
    def create_db_views(self, VIEWS_MISSING):
        metadata = MetaData()
        if HOSTS_FULL in VIEWS_MISSING:
            print("Adding view {}".format(HOSTS_FULL))

            # Get the table objects from the db engine
            components = Table(COMPONENTS, metadata, autoload=True, autoload_with=self.db_engine)
            hostscomponents = Table(HOSTSCOMPONENTS, metadata, autoload=True, autoload_with=self.db_engine)
            hosts = Table(HOSTS, metadata, autoload=True, autoload_with=self.db_engine)
            reservations = Table(RESERVATIONS, metadata, autoload=True, autoload_with=self.db_engine)

            # Create complete hosts view (with number of GPUS and FPGAS and is_free columns)

            # required sub queries
            # s_cpu = alias(select([components.c.componentID, components.c.name]).where(components.c.type == 0), name="scpus")
            s_gpu = alias(select([components.c.componentID, components.c.name, components.c.type]).where(components.c.type == 1), name="sgpus")
            s_fpga = alias(select([components.c.componentID, components.c.name, components.c.type]).where(components.c.type == 2), name="sfpgas")
            # s_frees = alias(select([hosts.c.hostname]).where(~exists(select([reservations.c.host]).where(reservations.c.host == hosts.c.hostname))), name="frees")
            
            # get the is_free column
            aux_frees1 = alias(select([hosts.c.hostname]), name="aux_frees1")
            aux_frees2 = alias(select([hosts.c.hostname]).where(~exists(select([reservations.c.host]).where(reservations.c.host == hosts.c.hostname))), name="aux_frees2")
            frees_join = aux_frees1.join(aux_frees2, aux_frees1.c.hostname == aux_frees2.c.hostname, isouter=True)
            s_frees = alias(select([aux_frees1.c.hostname, func.count(aux_frees2.c.hostname).label("is_free")]).select_from(frees_join).group_by(aux_frees1.c.hostname), name="s_frees")

            # required joins
            j1 = hosts.join(hostscomponents, hosts.c.hostname == hostscomponents.c.hostname, isouter=True)
            j2 = j1.join(s_gpu, hostscomponents.c.componentID == s_gpu.c.componentID, isouter=True)
            j3 = j2.join(s_fpga, hostscomponents.c.componentID == s_fpga.c.componentID, isouter=True)
            j4 = j3.join(s_frees, hosts.c.hostname == s_frees.c.hostname, isouter=True)
            # j5 = j4.join(s_cpu, s_cpu.c.componentID == hosts.c.cpu, isouter=True)

            # final select
            # THIS VIEW RETURNS ROWS IN THE FOLLOWING FORMAT: (hostname, ipaddr, cpuname, num_gpus, num_fpgas, enabled, is_free)
            stmt = select([
                    hosts.c.hostname,
                    hosts.c.ip,
                    hosts.c.cpu,
                    func.count(s_gpu.c.type).label("num_gpus"),
                    func.count(s_fpga.c.type).label("num_fpgas"),
                    hosts.c.enabled,
                    # func.count(s_frees.c.hostname).label("is_free")
                    s_frees.c.is_free.label("is_free")
                    ]).select_from(j4).group_by(hosts.c.hostname)
            
            view = create_view(HOSTS_FULL, stmt, metadata)

        if HOSTSCOMPS_FULL in VIEWS_MISSING:
            print("Adding view {}".format(HOSTSCOMPS_FULL))

            components = Table(COMPONENTS, metadata, autoload=True, autoload_with=self.db_engine)
            hostscomponents = Table(HOSTSCOMPONENTS, metadata, autoload=True, autoload_with=self.db_engine)

            # required joins
            j1 = hostscomponents.join(components, hostscomponents.c.componentID == components.c.componentID, isouter=True)

            stmt = select([
                            hostscomponents.c.hostname,
                            components.c.type,
                            components.c.componentID,
                            components.c.name
                        ]).select_from(j1).order_by(hostscomponents.c.hostname)
            
            view = create_view(HOSTSCOMPS_FULL, stmt, metadata)

        try:
            metadata.create_all(self.db_engine, checkfirst=True)
            print("Views added")
        except Exception as e:
            print("Error occurred during Views creation!")
            print(e)

    # Fill missing tables with default values
    def fill_defaults(self, TABLES_MISSING):
            for table in TABLES_MISSING:
                if table == HOSTSCOMPONENTS:
                    continue

                if table == COMPONENTS:
                    # add the default CPU component
                    self.insert("components(componentID,type,name,generation,manufacturer)", "(0,0,\"default\",\"\",\"\")")

                    files = ["cpus", "gpus", "fpgas"]
                    for i, f in enumerate(files):
                        def_file = read_csv("sqlite_db/defaults/def_{}.csv".format(f), ";")
                        print(def_file)
                        for row in def_file:
                            str_values = "({type}, \"{name}\", \"{gen}\", \"{manu}\")".format(type=i, name=row[1], gen=row[2],manu=row[0])
                            self.insert(COMPONENTS_SCHEMA, str_values)

                elif table != RESERVATIONS:
                    def_file = read_csv("sqlite_db/defaults/def_{}.csv".format(table), ";")
                    print(def_file)
                    for row in def_file:
                        if len(row) == 1:
                            values = "\"" + row[0] + "\""
                        else:
                            if table == HOSTS:
                                # row format: hostname, ip, has_gpu, has_fpga
                                values = "\"" + row[0] + "\"" + ', ' + row[1]
                               
                                # make all hosts enabled by default
                                values += ", 1"
                                # start with default CPUI
                                # values += ", \"default\""
                                values += ", 0"
                            else:
                                values = row[0]
                                for value in row[1:]:
                                    values += ", '{}'".format(value)

                        self.insert(table, "({})".format(values))

    # Insert, Update, Delete
    def execute_query(self, query='', log_args={}):
        if query == '': 
            return -1

        print(query)

        with self.db_engine.connect() as connection:
            try:
                if not DEBUG_MODE:
                    if log_args != {}:
                        # log the alteration into the log file
                        log_args["app"].logger.infosql("username:'{user}', execute:'{query}'".format(user=log_args["user"], query=query))

                result = connection.execute(query)
                return result.lastrowid

            except Exception as e:
                if not DEBUG_MODE:
                    logging.critical("Something awful happened", exc_info=True)
                print(e)
                return -1

    def print_query(self, table='', query='', num_cols=-1, log_args={}):
        query = query if query != '' else "SELECT * FROM '{}';".format(table)
        print(query)
        out = []
        with self.db_engine.connect() as connection:
            try:
                if not DEBUG_MODE:
                    if log_args != {}:
                        log_args["app"].logger.infosql("username:'{user}', query:'{query}'".format(user=log_args["user"], query=query))
                result = connection.execute(query)
            except Exception as e:
                if not DEBUG_MODE:
                    logging.critical("Something awful happened", exc_info=True)
                print(e)
            else:
                if (num_cols == 1) or (len(result.keys()) == 1):
                    out = [i[0] for i in result]
                else:
                    out = []
                    for row in result:
                        list_aux = []
                        for val in row:
                            list_aux.append(val)
                        out.append(list_aux)
                result.close()
        return out

    def insert(self, table, values, log_args={}):
        # Insert Data
        query = "INSERT INTO {} VALUES {};".format(table, values)
        return self.execute_query(query, log_args=log_args)

    def insert_newReservation(self, new_res, log_args={}):
        new_res_str = "(\"{user}\", \"{host}\", {restype}, \"{begin}\", \"{end}\")"\
            .format(user=new_res["user"], host=new_res["host"], restype=new_res["res_type"], begin=new_res["begin_date"], end=new_res["end_date"])

        return self.insert(RESERVATIONS_SCHEMA, new_res_str, log_args=log_args)

    def insert_newHost(self, new_host, log_args={}):
        # TODO: CHECK HOW TO SEND CPU
        hostname = new_host.pop("hostname")
        ipaddr = new_host.pop("ipaddr")
        cpuID = new_host.pop("cpu")

        new_host_str = "(\"{host}\", {ip}, 1, {cpu})".format(host=hostname, ip=ipaddr, cpu=cpuID)
        res = self.insert(HOSTS, new_host_str, log_args=log_args)

        if "gpu" in new_host.keys() or "fpga" in new_host.keys():
            print("HERE:")
            print(new_host)
            res = self.update_hostComponents(hostname, new_host, log_args=log_args)

        return res

    def insert_newComponent(self, new_comp, log_args={}):
        new_comp_str = "({type}, \"{name}\", \"{gen}\", \"{manu}\")".format(type=new_comp["type"], name=new_comp["name"], gen=new_comp["gen"],manu=new_comp["brand"])
        return self.insert(COMPONENTS_SCHEMA, new_comp_str, log_args=log_args)

    def insert_newUser(self, username, log_args={}):
        new_user_str = "(\"{user}\")".format(user=username)

        return self.insert(USERS, new_user_str, log_args=log_args)

    def del_entry(self, table, column, value, is_str=False, log_args={}):
        if is_str == True:
            delete = "DELETE FROM {} WHERE {}=\"{}\";".format(table, column, value)
        else:
            delete = "DELETE FROM {} WHERE {}={};".format(table, column, value)
        self.execute_query(delete, log_args=log_args)
        return True

    # Remove host from database
    def del_host(self, hostname, log_args={}):
        
        # Before removing host, remove all reservations associated with it
        list_res = self.get_listReservationsHost(hostname, "reservationID", log_args=log_args)
        for res_id in list_res:
            manual_removeReservation(res_id)

        # Before removing host, remove all host-components associated with it
        self.del_entry(HOSTSCOMPONENTS,  "hostname", "\""+hostname+"\"", log_args=log_args)

        return self.del_entry(HOSTS, "hostname", "\""+hostname+"\"", log_args=log_args)

    # Remove component from database
    def del_component(self, componentID, log_args={}):
        
        # Before removing component, remove all host-components associated with it
        self.del_entry(HOSTSCOMPONENTS,  "componentID", componentID, log_args=log_args)

        return self.del_entry(COMPONENTS, "componentID", componentID, log_args=log_args)


    # Remove restype from database
    def del_restype(self, restypeID, log_args={}):
        return self.del_entry(RESTYPES, "restypeID", restypeID, log_args=log_args)

    def toggle_enableHost(self, hostname, log_args={}):
        query = "SELECT enabled FROM {} WHERE hostname=\"{}\";".format(HOSTS, hostname)
        enabled = self.print_query(query=query, log_args=log_args)[0]
        print(enabled)
        enabled = 1 - enabled
        update = "UPDATE {} SET enabled = {} WHERE hostname=\"{}\"".format(HOSTS, enabled, hostname)
        self.execute_query(update, log_args=log_args)
        return True

    def update_configHost(self, hostname, ipaddr, cpu, optional_comps, log_args={}):
        # TODO: CHECK THIS FUNCTION

        # update IP
        update = "UPDATE {} SET ip = {} WHERE hostname=\"{}\"".format(HOSTS, ipaddr, hostname)
        res = self.execute_query(update, log_args=log_args)
        if res == -1:
            return res
            
        # update CPU
        update = "UPDATE {} SET cpu = {} WHERE hostname=\"{}\"".format(HOSTS, cpu, hostname)
        res = self.execute_query(update, log_args=log_args)
        if res == -1:
            return res

        if optional_comps != {}:
            res = self.update_hostComponents(hostname, optional_comps, log_args=log_args)
            
        return res

    def update_hostComponents(self, hostname, components, log_args={}):
        # TODO: Confirm this function

        # first delete all entries of the host in the HOSTSCOMPONENTS table
        self.del_entry(HOSTSCOMPONENTS, "hostname", hostname, True, log_args=log_args)

        # now add the new components
        if "gpu" in components.keys():
            for gpu in components["gpu"]:
                self.insert(HOSTSCOMPONENTS, "(\"{hostname}\", {compID})".format(hostname=hostname, compID=gpu), log_args=log_args)

        if "fpga" in components.keys():
            for fpga in components["fpga"]:
                self.insert(HOSTSCOMPONENTS, "(\"{hostname}\", {compID})".format(hostname=hostname, compID=fpga), log_args=log_args)

        return True

    def update_configComponent(self, componentID, name, brand, gen, log_args={}):

        # update name
        update = "UPDATE {table} SET name = \"{name}\" WHERE componentID={id}".format(table=COMPONENTS, name=name, id=componentID)
        res = self.execute_query(update, log_args=log_args)
        if res == -1:
            return res

        # update brand
        update = "UPDATE {table} SET manufacturer = \"{brand}\" WHERE componentID={id}".format(table=COMPONENTS, brand=brand, id=componentID)
        res = self.execute_query(update, log_args=log_args)
        if res == -1:
            return res

        # update gen
        update = "UPDATE {table} SET generation = \"{gen}\" WHERE componentID={id}".format(table=COMPONENTS, gen=gen, id=componentID)
        res = self.execute_query(update, log_args=log_args)

        return res

    def update_configRestype(self, restypeID, name, description, log_args={}):

        # update name
        update = "UPDATE {table} SET name = \"{name}\" WHERE restypeID={id}".format(table=RESTYPES, name=name, id=restypeID)
        res = self.execute_query(update, log_args=log_args)
        if res == -1:
            return res

        # update description
        update = "UPDATE {table} SET description = \"{description}\" WHERE restypeID={id}".format(table=RESTYPES, description=description, id=restypeID)
        res = self.execute_query(update, log_args=log_args)
        if res == -1:
            return res

        return res

    # QUERIES~
    # Get list of users in the DB
    def get_listUsers(self, log_args={}):
        query = "SELECT username FROM {users} ORDER BY username;".format(users=USERS)
        return self.print_query(query=query, log_args=log_args)
    
    # Get list of enabled hosts
    def get_listEnabledHosts(self, log_args={}):
        query = "SELECT hostname FROM {hosts} WHERE enabled=1 ORDER BY hostname;".format(hosts=HOSTS)
        return self.print_query(query=query, log_args=log_args)

    def get_listComponents(self, type_code="", log_args={}):
        if type_code == "":
            query = "SELECT componentID, name FROM {components} ORDER BY name".format(components=COMPONENTS)
        else:
            query = "SELECT componentID, name FROM {components} WHERE type={type} ORDER BY name".format(components=COMPONENTS, type=type_code)

        result_query = self.print_query(query=query, log_args=log_args)

        list_ids = [i[0] for i in result_query]
        list_names = [i[1] for i in result_query]
        return list_names, list_ids

    def get_listHostsComponents(self, log_args={}):
        query = "SELECT * FROM {hostscomponents} ORDER BY hostname;".format(hostscomponents=HOSTSCOMPS_FULL)
        return self.print_query(query=query, log_args=log_args)
        
    # Get full list host information
    def get_fullListHosts(self, log_args={}):
        query = "SELECT * FROM {hosts} ORDER BY hostname;".format(hosts=HOSTS_FULL)
        return self.print_query(query=query, log_args=log_args)

    def get_fullListComponents(self, type_code="", log_args={}):
        if type_code == "":
            query = "SELECT * FROM {components} ORDER BY name".format(components=COMPONENTS)
        else:
            query = "SELECT * FROM {components} WHERE type={type} ORDER BY name".format(components=COMPONENTS, type=type_code)
        return self.print_query(query=query, log_args=log_args)

    # Get list of different types of reservations
    def get_fullListResTypes(self, log_args={}):
        query = "SELECT * FROM {restypes};".format(restypes=RESTYPES)
 
        return self.print_query(query=query, log_args=log_args)

    # Get list of current free hosts (that are enabled)
    def get_listFreeHosts(self, log_args={}):
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
        return self.print_query(query=query, num_cols=1, log_args=log_args)
   
    # Get list of all current scheduled reservations 
    def get_listCurrentReservations(self, username="", log_args={}):
        str_where = ""
        if not username=="":
            str_where = "WHERE {users}.username=\"{username}\"".format(users=USERS, username=username)
        # query = "SELECT \
        #             {hosts}.hostname, \
        #             {users}.username, \
        #             res_t.name, \
        #             res.begin_date, \
        #             res.end_date, \
        #             res.reservationID \
        #         FROM \
        #             {res} as res \
        #             LEFT JOIN {hosts} ON {hosts}.hostname = res.host \
        #             LEFT JOIN {users} ON {users}.username = res.user \
        #             LEFT JOIN {restypes} as res_t ON res_t.restypeID = res.reservation_type \
        #         {where} \
        #         ORDER BY 1,2;".format(res=RESERVATIONS, hosts=HOSTS, users=USERS, restypes=RESTYPES, where=str_where)
        query = "SELECT {hosts}.hostname, {users}.username, res_t.name, res.begin_date, res.end_date, res.reservationID \
                FROM {res} as res LEFT JOIN {hosts} ON {hosts}.hostname = res.host LEFT JOIN {users} ON {users}.username = res.user LEFT JOIN {restypes} as res_t ON res_t.restypeID = res.reservation_type \
                {where} ORDER BY 1,2;".format(res=RESERVATIONS, hosts=HOSTS, users=USERS, restypes=RESTYPES, where=str_where)
        return self.print_query(query=query, log_args=log_args)

    def get_listReservationsHost(self, hostname, column, log_args={}):
        query = "SELECT {col} \
                FROM {res} \
                WHERE host=\"{host}\";".format(res=RESERVATIONS, col=column, host=hostname)
        return self.print_query(query=query, log_args=log_args)

# CREATE/OPEN THE DATABASE
dbmain = ReservationsDB(SQLITE, dbname="sqlite/db/res_alloc.db")

# Function activated by the scheduler when END Time of a reservation activates
def timed_removeReservation(*args):
    res_id = args[0]
    print("Time's up! Finishing reservation with id {}".format(res_id))

    if not DEBUG_MODE:
        try:
            # New entry in the log file (this is done differently because it is from outside the app context)
            logger = logging.getLogger("app.sqlite")
            logger.infosql("username:'{user}', execute:'DELETE FROM {table} WHERE res_id={res_id}'".format(user="auto_timer", table=RESERVATIONS, res_id=res_id))
        except:
            logging.critical("Something awful happened", exc_info=True)
            return -1        

    return dbmain.del_entry(RESERVATIONS, "reservationID", res_id)

# Function activated when user manually cancels reservation    
def manual_removeReservation(res_id, log_args):
    from flask_app.app import scheduler

    try:
        # must also remove scheduled remove action from the scheduler
        scheduler.remove_job(id='j'+str(res_id))
    except Exception as e:
        if not DEBUG_MODE:
            logging.critical("Something awful happened", exc_info=True)
        print(e)
        return -1
    
    return dbmain.del_entry(RESERVATIONS, "reservationID", res_id, log_args=log_args)

# Function to check if a new reservation conflicts with any of the previous ones
# (Return True if there is a conflict)
def check_conflictsNewReservation(new_res, log_args):    
    list_res = dbmain.get_listReservationsHost(new_res["host"], "*", log_args=log_args)
    

    for res in list_res:
        # Check if there is any intersection of the timeslot
        if (new_res["end_date"] <= res[IDX_BEGIN_DATE]) or (new_res["begin_date"] >= res[IDX_END_DATE]):
            continue
        else:
            # if there is, need to check if the reservation types results in conflicts or not

            # Uncomment to debug
            # print("\tPossible conflict (Time is conflicting with res {})".format(res[0]))
            # print("\tres: '{}'".format(res))
            # print("\tnew_res: '{}'".format(new_res))
            # print("\t\tres[res_type]: '{}'".format(res[IDX_RESTYPE]))
            # print("\t\tnew_res[res_type]: '{}'".format(new_res["res_type"]))

            # if either of the reservations (old conflicting one or new one) is of type 1 (RESERVED FULL)
            # conflict_res = "<br/><br/>Conflicting reservation (reservationID, username, hostname, reservation_type, begin_date, end_date):<br/>    {}".format(res)
            conflict_res = " Conflicting reservation (reservationID, username, hostname, reservation_type, begin_date, end_date): {}".format(res)
            if (res[IDX_RESTYPE] == 1) or (int(new_res["res_type"]) == 1):
                error_str = "New reservation conflicts with existing reservation. (One of them is of type 'RESERVED FULL SYSTEM')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res
            
            # if both reservations (old conflicting one and new one) are locking the FPGA (RESERVED FPGA)
            if (res[IDX_RESTYPE] == 2) and (int(new_res["res_type"]) == 2):
                error_str = "New reservation conflicts with existing reservation. (Both of them are of type 'RESERVED FPGA')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res
            
            # if both reservations (old conflicting one and new one) are locking the GPU (RESERVED GPU)
            if (res[IDX_RESTYPE] == 3) and (int(new_res["res_type"]) == 3):
                error_str = "New reservation conflicts with existing reservation. (Both of them are of type 'RESERVED GPU')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res

            # if old res is RESERVED_GPU or RESERVED_FPGA and new one is DEVELOPING or RUNNING PROGRAMS
            if ((res[IDX_RESTYPE] == 2) or (res[IDX_RESTYPE] == 3)) and ((int(new_res["res_type"]) == 4) or (int(new_res["res_type"]) == 5)):
                error_str = "New reservation conflicts with existing reservation. (New reservation is of type 'DEVELOPING' or 'RUNNING PROGRAMS/SIMULATIONS', which conflicts with reservations of type 'RESERVED FPGA' or 'RESERVED GPU')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res

            # if old res is DEVELOPING or RUNNING PROGRAMS and new one is RESERVED_GPU or RESERVED_FPGA 
            if ((res[IDX_RESTYPE] == 4) or (res[IDX_RESTYPE] == 5)) and ((int(new_res["res_type"]) == 2) or (int(new_res["res_type"]) == 3)):
                error_str = "New reservation conflicts with existing reservation. (Existing reservation is of type 'DEVELOPING' or 'RUNNING PROGRAMS/SIMULATIONS', which conflicts with new reservation of type 'RESERVED FPGA' or 'RESERVED GPU')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res
            # if 

    return False, ""

def check_hostStatusNextWeek(host, log_args):
    from datetime import datetime, timedelta
    
    next_week = [0] * 7 # one field for each day of the next week. 0-free, 1-reserved full, 2-reserved fpga, 3-reserved gpu, 4-running programs, 5-developing, 6-reserved gpu and fpga
    
    time_now = datetime.now()
    current_day = time_now.strftime("%Y-%m-%d")
    time_in_one_week = time_now + timedelta(days=7)
    nextweek_day = time_in_one_week.strftime("%Y-%m-%d")
    print(current_day)
    print(nextweek_day)

    list_res = dbmain.get_listReservationsHost(host, "*", log_args=log_args)
    for res in list_res:
        # check if reservation falls into the next week
        if (res[IDX_BEGIN_DATE] >= nextweek_day) or (res[IDX_END_DATE] <= current_day):
            continue

        # if it reaches here there is already some days where the host is in use during the next week
        day_aux = time_now
        for day_i in range(0,7):
            str_day_aux = day_aux.strftime("%Y-%m-%d")
            day_aux += timedelta(days=1)
            
            if next_week[day_i] == 1:
                continue     

            if (str_day_aux >= res[IDX_BEGIN_DATE]) and (str_day_aux <= res[IDX_END_DATE]):
                
                if next_week[day_i] == 0:
                    # if day was still assigned as free
                    next_week[day_i] = res[IDX_RESTYPE]
                
                elif ((next_week[day_i] == 2) and (res[IDX_RESTYPE] == 3)) or ((next_week[day_i] == 3) and (res[IDX_RESTYPE] == 2)):
                    # if day has GPU and FPGA reserved
                    next_week[day_i] = 6

                elif next_week[day_i] == 7:
                    # if day already had GPU and FPGA reserved only allow CPU reserved
                    if (res[IDX_RESTYPE] == 1): 
                        next_week[day_i] = 1

                elif next_week[day_i] < res[IDX_RESTYPE]:
                    # if day still had lower priority than this reservation
                    next_week[day_i] = res[IDX_RESTYPE]
             
        if next_week == [1] * 7:
            # this would be already the worst case scenario, no point in continuing through the reservations
            break

    return next_week