import logging

from flask_app.app import db
from flask_app.src.custom_logs import write_log, write_log_exception, LOG_UDPATE_FORMAT, LOG_UDPATE_FORMAT_STR

from flask_app.src.models import *
from flask_app.src.models import User, Host, Component, Reservation_type, Reservation
from flask_app.src.models.sql_query import get_entryObject


def update_toggleEnableHost(hostID, log_args={}):
    # TODO: Does it make sense to filter by hostname and not id?
    try:
        log_args["values"] = {"hostID": hostID}
        host_obj = get_entryObject(Host, hostID, log_args=log_args)
        if host_obj.enabled == 1:
            log_args["values"]["enabled"] = LOG_UDPATE_FORMAT.format("'Yes'", "'No'")
        else:
            log_args["values"]["enabled"] = LOG_UDPATE_FORMAT.format("'No'", "'Yes'")
        host_obj.enabled = 1 - Host.enabled

        write_log(log_args, "UDPATE", Host.__table__.name)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        write_log_exception(e)

    return 

def update_hostComponents(host_obj, list_gpus, list_fpgas, values_updated = {}, log_args={}):
    list_hostcomponents = host_obj.components.all()
    list_gpus_old = sorted([i.id for i in list_hostcomponents if i.type == CODE_GPU])
    list_fpgas_old = sorted([i.id for i in list_hostcomponents if i.type == CODE_FPGA])
    list_gpus_new = sorted([int(i) for i in list_gpus])
    list_fpgas_new = sorted([int(i) for i in list_fpgas])

    if list_gpus_old != list_gpus_new:
        list_gpu_objs = []
        for gpuID in list_gpus:
            # get the corresponding gpu object
            gpu_object = get_entryObject(Component, gpuID, log_args=log_args)
            list_gpu_objs.append(gpu_object)
        
        values_updated["gpu"] = LOG_UDPATE_FORMAT.format(list_gpus_old, list_gpus_new)
        # write_log(log_args, "UDPATE", Host.__table__.name, {"hostID":host_obj.id, "gpu": LOG_UDPATE_FORMAT.format(list_gpus_old, list_gpus_new)})
    else:
        list_gpu_objs = [i for i in list_hostcomponents if i.type == CODE_GPU]
    
    if list_fpgas_old != list_fpgas_new:
        list_fpga_objs = []
        for fpgaID in list_fpgas:
            # get the corresponding fpga object
            fpga_object = get_entryObject(Component, fpgaID, log_args=log_args)
            list_fpga_objs.append(fpga_object)
            
        values_updated["fpga"] = LOG_UDPATE_FORMAT.format(list_fpgas_old, list_fpgas_new)
        # write_log(log_args, "UDPATE", Host.__table__.name, {"hostID":host_obj.id, "fpga": LOG_UDPATE_FORMAT.format(list_fpgas_old, list_fpgas_new)})
    else:
        list_fpga_objs = [i for i in list_hostcomponents if i.type == CODE_FPGA]

    # finally make the assignment to the host
    host_obj.components = list_gpu_objs + list_fpga_objs

    return host_obj, values_updated

def update_configHost(hostID, hostname="", ip="", cpu="", gpus=[], fpgas=[], log_args={}):
    try:    
        values_updated = {"hostID": hostID}

        host_obj = get_entryObject(Host, hostID, log_args=log_args)

        if (hostname != "") and (host_obj.hostname != hostname):
            # update hostname and save the change for logging
            values_updated["hostname"] = LOG_UDPATE_FORMAT_STR.format(host_obj.hostname, hostname)
            host_obj.hostname = hostname
            
        if (ip != "") and (host_obj.ip != ip):
            # update IP and save the change for logging
            values_updated["ip"] = LOG_UDPATE_FORMAT.format(host_obj.ip, ip)
            host_obj.ip = ip

        if (cpu != "") and (host_obj.cpu != cpu):
            # update CPU and save the change for logging
            values_updated["cpu"] = LOG_UDPATE_FORMAT.format(host_obj.cpu, cpu)
            host_obj.cpu = cpu
        
        
        if (gpus != []) or (fpgas != []):
            # update assigned components (GPU and FPGAs)
            host_obj, values_updated = update_hostComponents(host_obj, gpus, fpgas, log_args=log_args, values_updated=values_updated)
        
        if len(values_updated.keys()) > 1:
            # if changes were made log them in the file
            log_args["values"] = values_updated
            write_log(log_args, "UDPATE", Host.__table__.name)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        write_log_exception(e)

    return 

def update_configComponent(componentID, name, manufacturer, generation, log_args={}):
    try:    
        values_updated = {"componentID": componentID}

        component_obj = get_entryObject(Component, componentID, log_args=log_args)
        if component_obj.name != name:
            # update name
            values_updated["name"] = LOG_UDPATE_FORMAT_STR.format(component_obj.name, name)
            component_obj.name = name
        if component_obj.manufacturer != manufacturer:
            # update manufacturer
            values_updated["manufacturer"] = LOG_UDPATE_FORMAT_STR.format(component_obj.manufacturer, manufacturer)
            component_obj.manufacturer = manufacturer
        if component_obj.generation != generation:
            # update gen
            values_updated["generation"] = LOG_UDPATE_FORMAT_STR.format(component_obj.generation, generation)
            component_obj.generation = generation
        
        if len(values_updated.keys()) > 1:
            log_args["values"] = values_updated
            write_log(log_args, "UDPATE", Component.__table__.name)
            db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        write_log_exception(e)
    return 

def update_configRestype(restypeID, name, description, log_args={}):
    try:
        values_updated = {"restypeID": restypeID}

        restype_obj = get_entryObject(Reservation_type, restypeID, log_args=log_args)
        
        if restype_obj.name != name:
            # update name
            values_updated["name"] = LOG_UDPATE_FORMAT_STR.format(restype_obj.name, name)
            restype_obj.name = name
        if restype_obj.description != description:
            # update description
            values_updated["description"] = LOG_UDPATE_FORMAT_STR.format(restype_obj.description, description)
            restype_obj.description = description

        if len(values_updated.keys()) > 1:
            log_args["values"] = values_updated
            write_log(log_args, "UDPATE", Reservation_type.__table__.name)
            db.session.commit()

    except Exception as e:
        db.session.rollback()
        write_log_exception(e)

    return 