import logging

from flask_app.app import db
from flask_app.src.models import User, Host, Component, Reservation_type, Reservation


# Query the Database and get a single column from a table
# Can filter the results (e.g., WHERE <filter_col> == <filter_value>)
def get_singleColumn(Table, column_name, log_args={}, filter_col="", filter_value="", return_obj = False):
    if filter_col == "":
        result = db.session.query(getattr(Table,column_name)).order_by(getattr(Table,column_name)).all()
    else:
        result = db.session.query(getattr(Table,column_name)).filter(getattr(Table,filter_col)==filter_value).order_by(getattr(Table,column_name)).all()
    if not return_obj:
        result = [i._asdict()[column_name] for i in result]
    return result

# Query the Database and get all columns from a table
# Can filter the results (e.g., WHERE <filter_col> == <filter_value>)
# Can order the results by a specific column
def get_fullTable(Table, log_args={}, filter_col="", filter_value="", order_by_col="", return_obj = False):
    if filter_col == "":
        if order_by_col == "":
            result = db.session.query(Table).all()
        else:
            result = db.session.query(Table).order_by(getattr(Table,order_by_col)).all()
    elif filter_col == "id":
        if order_by_col == "":
            result = db.session.query(Table).get(filter_value)
        else:
            result = db.session.query(Table).get(filter_value).order_by(getattr(Table,order_by_col))
    else:
        if order_by_col == "":
            result = db.session.query(Table).filter(getattr(Table,filter_col)==filter_value).all()
        else:
            result = db.session.query(Table).filter(getattr(Table,filter_col)==filter_value).order_by(getattr(Table,order_by_col)).all()
    if not return_obj:
        result = [i._asdict() for i in result]
    return result

# ----- Some simple auxiliary functions -----
def get_idFromHostname(hostname, log_args={}):
    return get_singleColumn(Host, "id", filter_col="hostname", filter_value=hostname, log_args=log_args)[0]

def get_idFromUsername(username, log_args={}):
    return get_singleColumn(User, "id", filter_col="username", filter_value=username, log_args=log_args)[0]


# ----- These functions use the two defined previously -----
def get_listUsers(log_args={}):
    return get_singleColumn(User, "username") 

def get_listHosts(enabled = False, log_args={}):
    if enabled == True:
        return get_singleColumn(Host, "hostname", filter_col="enabled", filter_value=1, log_args=log_args) 
    else:
        return get_singleColumn(Host, "hostname", log_args=log_args) 

def get_fullListHosts(enabled = False, log_args={}):
    if enabled == True:
        return get_fullTable(Host, order_by_col="hostname", filter_col="enabled", filter_value=1, log_args=log_args)
    else:
        return get_fullTable(Host, order_by_col="hostname", log_args=log_args)

def get_fullListComponents(type_code="", log_args={}):
    if type_code == "":
        return get_fullTable(Component, order_by_col="name", log_args=log_args)
    else:
        return get_fullTable(Component, filter_col="type", filter_value=type_code, order_by_col="name", log_args=log_args)

def get_fullListResTypes(log_args={}):
    return get_fullTable(Reservation_type, log_args=log_args)


# ----- These next functions use more specific queries -----

# Get list of components in the Database (id and name)
def get_listComponents(type_code="", log_args={}):
    if type_code == "":
        result = db.session.query(Component.id, Component.name).order_by(Component.name).all()
    else:
        result = db.session.query(Component.id, Component.name).filter(Component.type == type_code).order_by(Component.name).all()
    dict_components = {}
    dict_components["id"] = [i._asdict()["id"] for i in result]
    dict_components["name"] = [i._asdict()["name"] for i in result]
    return dict_components

# Get components (GPU and FPGAs) assigned to each host
# Returns two dictionaries, one for GPUs and one for FPGAs, where the keys are the hostnames 
#  and each entry is the list of components assigned to that host
def get_listHostsComponents(log_args={}):
    all_hosts = db.session.query(Host).all()
    dict_hostgpus = {host._asdict()["hostname"]: [] for host in all_hosts}
    dict_hostfpgas = {host._asdict()["hostname"]: [] for host in all_hosts}
    for host in all_hosts:
        hostname = host._asdict()["hostname"]
        list_comps = host.components.all()
        for comp in list_comps:
            comp_dict = comp._asdict()
            if comp_dict["type"] == 1:
                dict_hostgpus[hostname].append(comp_dict["id"])
            else:
                dict_hostfpgas[hostname].append(comp_dict["id"])
    return dict_hostgpus, dict_hostfpgas
    

# # Get list of current free hosts (that are enabled)
# def get_listFreeHosts(self, log_args={}):
#     query = "SELECT \
#                 {hosts}.hostname, \
#                 COUNT(res.host) as num_reservations \
#             FROM \
#                 {hosts} \
#                 LEFT JOIN {res} as res ON {hosts}.hostname = res.host \
#             WHERE {hosts}.enabled = 1 \
#             GROUP BY {hosts}.hostname \
#             HAVING num_reservations == 0 \
#             ORDER BY {hosts}.hostname;".format(res=RESERVATIONS, hosts=HOSTS)
#     return self.print_query(query=query, num_cols=1, log_args=log_args)



# Get list of all current scheduled reservations 
def get_listCurrentReservations(username="", log_args={}):
    if username == "":
        # query = "SELECT \
        #             res.reservationID \
        #             {hosts}.hostname, \
        #             {users}.username, \
        #             res_t.name, \
        #             res.begin_date, \
        #             res.end_date, \
        #         FROM \
        #             {res} as res \
        #             LEFT JOIN {hosts} ON {hosts}.hostname = res.host \
        #             LEFT JOIN {users} ON {users}.username = res.user \
        #             LEFT JOIN {restypes} as res_t ON res_t.restypeID = res.reservation_type \
        #         {where} \
        #         ORDER BY 2,3;".format(res=RESERVATIONS, hosts=HOSTS, users=USERS, restypes=RESTYPES, where=str_where)
        result = db.session.query( 
                Reservation.id, 
                Host.hostname, 
                User.username, 
                Reservation_type.name, 
                Reservation.begin_date,  
                Reservation.end_date
            ).join(
                Host, Host.id == Reservation.hostID, isouter=True
            ).join(
                User, User.id == Reservation.userID, isouter=True
            ).join(
                Reservation_type, Reservation_type.id == Reservation.reservation_type, isouter=True
            ).order_by(
                Host.hostname, Reservation.begin_date
            ).all()
    else:
        result = db.session.query( 
                Reservation.id, 
                Host.hostname, 
                User.username, 
                Reservation_type.name, 
                Reservation.begin_date,  
                Reservation.end_date 
            ).join( 
                Host, Host.id == Reservation.hostID, isouter=True 
            ).join( 
                User, User.id == Reservation.userID, isouter=True 
            ).join( 
                Reservation_type, Reservation_type.id == Reservation.reservation_type, isouter=True 
            ).filter(
                User.username == username
            ).order_by(
                Host.hostname,
                Reservation.begin_date
            ).all()
    result = [i._asdict() for i in result]
    return result

def get_listReservationsHost(hostID, return_obj = False, log_args={}):
    result = db.session.query(Host).get(hostID).host_reservations.all()
    if not return_obj:
        result = [i._asdict() for i in result]
    return result

def get_entryObject(Table, id, log_args={}):
    return get_fullTable(Table, filter_col="id", filter_value=id, return_obj=True, log_args=log_args)