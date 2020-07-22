import logging

from flask_app.app import db
from flask_app.src.models import User, Host, Component, Reservation_type, Reservation
from flask_app.src.global_stuff import DEBUG_MODE

from flask_app.src.models.sql_query import get_entryObject, get_listReservationsHost


def del_entry(entry_obj, final=True, log_args={}):
    db.session.delete(entry_obj)
    if final:
        return db.session.commit()
    else:   
        return db.session.flush()

# Remove host from database
def del_host(hostID, log_args={}):
    host_obj = get_entryObject(Host, hostID, log_args=log_args)

    # Before removing host, remove all reservations associated with it
    list_res_obj = get_listReservationsHost(hostID, return_obj=True, log_args=log_args)
    for res_obj in list_res_obj:
        manual_removeReservation(res_obj, final=False, log_args=log_args)

    # Before removing host, remove all components assigned to it
    host_obj.components = []
    # TODO: CHECK IF THIS ORDER REMOVES THE ENTRIES FROM HOSTCOMPONENT TABLE
    
    return del_entry(host_obj, final=True, log_args=log_args)

# Remove component from database
def del_component(componentID, log_args={}):
    component_obj = get_entryObject(Component, componentID, log_args=log_args)
    
    # Before removing component, remove all associations with it
    # case CPUs
    for host in component_obj.hosts:
        host.cpu = 0 # make cpu of this host the default CPU
    # case GPUs or FPGAs 
    component_obj.assigned_to = []
    return del_entry(component_obj, final=True, log_args=log_args)
    



# Remove restype from database
def del_restype(restypeID, log_args={}):
    restype_obj = get_entryObject(Reservation_type, restypeID, log_args=log_args)
    return del_entry(restype_obj, final=True, log_args=log_args)

# Function activated when user manually cancels reservation    
def manual_removeReservation(res_obj, final=True, log_args={}):
    from flask_app.app import scheduler

    res_id = res_obj.id
    try:
        # must also remove scheduled remove action from the scheduler
        scheduler.remove_job(id='j'+str(res_id))
    except Exception as e:
        if not DEBUG_MODE:
            logging.critical("Something awful happened", exc_info=True)
        print(e)
        # return -1

    return del_entry(res_obj, final=final, log_args=log_args)

def timed_removeReservation(*args):
    resID = args[0]
    print("Time's up! Finishing reservation with id {}".format(resID))
    res_obj = get_entryObject(Reservation, resID, log_args=log_args)
    if not DEBUG_MODE:
        try:
            # New entry in the log file (this is done differently because it is from outside the app context)
            logger = logging.getLogger("app.sqlite")
            logger.infosql("username:'{user}', execute:'DELETE FROM {table} WHERE res_id={resID}'".format(user="auto_timer", table="reservation", resID=resID))
        except:
            logging.critical("Something awful happened", exc_info=True)
            return -1        
    return del_entry(res_obj, final=True, log_args=log_args)