import logging

from flask_app.app import db
from flask_app.src.models import User, Host, Component, Reservation_type, Reservation
from flask_app.src.global_stuff import DEBUG_MODE

from flask_app.src.models.sql_query import get_entryObject

def update_toggleEnableHost(hostID, log_args={}):
    # TODO: Does it make sense to filter by hostname and not id?
    host_obj = get_entryObject(Host, hostID, log_args=log_args)
    host_obj.enabled = 1 - Host.enabled
    return db.session.commit()

def update_hostComponents(host_obj, components, log_args={}):
    host_obj.components = []
    for gpuID in components["gpu"]:
        # get the corresponding gpu object
        gpu_object = get_entryObject(Component, gpuID, log_args=log_args)
        host_obj.components.append(gpu_object)
    
    for fpgaID in components["fpga"]:
        # get the corresponding fpga object
        fpga_object = get_entryObject(Component, fpgaID, log_args=log_args)
        host_obj.components.append(fpga_object)
    return host_obj

def update_configHost(hostID, hostname, ipaddr, cpu, optional_comps, log_args={}):
    # TODO: Does it make sense to filter by hostname and not id?
    host_obj = get_entryObject(Host, hostID, log_args=log_args)
    
    # update hostname
    host_obj.hostname = hostname
    # update IP
    host_obj.ip = ipaddr
    # update CPU
    host_obj.cpu = cpu
    # update assigned components (GPU and FPGAs)
    if optional_comps != {}:
        host_obj = update_hostComponents(host_obj, optional_comps, log_args=log_args)
    return db.session.commit()

def update_configComponent(componentID, name, manufacturer, generation, log_args={}):
    component_obj = get_entryObject(Component, componentID, log_args=log_args)
    # update name
    component_obj.name = name
    # update manufacturer
    component_obj.manufacturer = manufacturer
    # update gen
    component_obj.generation = generation
    return db.session.commit()

def update_configRestype(restypeID, name, description, log_args={}):
    restype_obj = get_entryObject(Reservation_type, restypeID, log_args=log_args)
    # update name
    restype_obj.name = name
    # update description
    restype_obj.description = description
    return db.session.commit()