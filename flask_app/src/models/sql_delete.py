import logging

from flask_app.app import db
from flask_app.src.models import User, Host, Component, Reservation_type, Reservation
from flask_app.src.custom_logs import write_log, write_log_exception, LOG_UDPATE_FORMAT, LOG_UDPATE_FORMAT_STR

from flask_app.src.models import *
from flask_app.src.models.sql_query import get_entryObject, get_listReservationsHost
from flask_app.src.models.sql_update import update_hostComponents, update_configHost


def del_entry(entry_obj, final=True, log_args={}):
    try:
        log_args["values"] = {"id": entry_obj.id}
        write_log(log_args, "DELETE", entry_obj.__table__.name)

        db.session.delete(entry_obj)

        if final:
            return db.session.commit()
        else:   
            return db.session.flush()

    except Exception as e:
        db.session.rollback()
        write_log_exception(e)

# Remove host from database
def del_host(hostID, log_args={}):
    host_obj = get_entryObject(Host, hostID, log_args=log_args)

    # Before removing host, remove all reservations associated with it
    list_res_obj = get_listReservationsHost(hostID, return_obj=True, log_args=log_args)
    for res_obj in list_res_obj:
        manual_removeReservation(res_obj, final=False, log_args=log_args)

    # Before removing host, remove all components assigned to it
    # host_obj.components = []
    values_updated = {"hostID": hostID}
    update_hostComponents(host_obj, [], [], values_updated=values_updated, log_args=log_args)
    
    # TODO: CHECK IF THIS ORDER REMOVES THE ENTRIES FROM HOSTCOMPONENT TABLE
    
    return del_entry(host_obj, final=True, log_args=log_args)

# Remove component from database
def del_component(componentID, log_args={}):
    component_obj = get_entryObject(Component, componentID, log_args=log_args)
    
    # Before removing component, remove all associations with it
    
    if component_obj.type == CODE_CPU:
        # case CPUs
        for host in component_obj.hosts:
            update_configHost(host.id, cpu=0, log_args=log_args)
            host.cpu = 0 # make cpu of this host the default CPU

    elif component_obj.type == CODE_GPU:
        # case GPUs
        for host in component_obj.assigned_to:
            old_assigned_gpus = [i.id for i in host.components.all() if i.type == CODE_GPU]
            new_assigned_gpus = old_assigned_gpus.copy()
            new_assigned_gpus.remove(componentID)
            log_args["values"] = {"hostID": host.id, "gpu": LOG_UDPATE_FORMAT.format(old_assigned_gpus, new_assigned_gpus)}
            write_log(log_args, "UPDATE", Host.__table__.name)
        component_obj.assigned_to = []
    
    elif component_obj.type == CODE_FPGA:
        # case FPGAs
        for host in component_obj.assigned_to:
            old_assigned_fpgas = [i.id for i in host.components.all() if i.type == CODE_FPGA]
            new_assigned_fpgas = old_assigned_fpgas.copy()
            new_assigned_fpgas.remove(componentID)
            log_args["values"] = {"hostID": host.id, "fpga": LOG_UDPATE_FORMAT.format(old_assigned_fpgas, new_assigned_fpgas)}
            write_log(log_args, "UPDATE", Host.__table__.name)
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
        write_log_exception(e)
        # return -1

    return del_entry(res_obj, final=final, log_args=log_args)

def timed_removeReservation(*args):
    import logging
    from flask_app.src.global_stuff import DEBUG_MODE
    from flask_app.app import app

    try:
        resID = args[0]
        
        # this is done differently because it is from outside the app context
        with app.app_context():
            res_obj = get_entryObject(Reservation, resID)
            if not DEBUG_MODE:
                logger = logging.getLogger("app.sqlite")
                # New entry in the log file 
                logger.infosql("username:'{user}', DELETE in Table:'reservation', values={{ 'resID': {id} }}".format(user="auto_timer", id=resID))
            db.session.delete(res_obj)
            db.session.commit()

    except Exception as e:
        write_log_exception(e)    
    
    return