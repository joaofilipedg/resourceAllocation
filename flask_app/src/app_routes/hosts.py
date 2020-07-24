from flask import render_template, request, redirect, url_for, current_app
from flask_login import current_user, login_required
from datetime import datetime

# import flask_app.src.sql_sqlalchemy as mydb
# from flask_app.src.sql_sqlalchemy import dbmain, CODE_CPU, CODE_GPU, CODE_FPGA

from flask_app.src.models import *
from flask_app.src.models.sql_query import get_fullListHosts, get_listComponents, get_listHostsComponents
from flask_app.src.models.sql_insert import insert_newEntry
from flask_app.src.models.sql_update import update_toggleEnableHost, update_configHost
from flask_app.src.models.sql_delete import del_host
from flask_app.src.models.aux_checks import check_hostStatusNextWeek


from . import app_routes

# Edit page, to edit list of hosts, add new host,
@app_routes.route('/edit_hosts')
@login_required
def edit_hosts():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    full_list_hosts = get_fullListHosts(log_args=log_args)

    dict_cpus = get_listComponents(CODE_CPU, log_args=log_args)
    dict_gpus = get_listComponents(CODE_GPU, log_args=log_args)
    dict_fpgas = get_listComponents(CODE_FPGA, log_args=log_args)

    list_cpus = dict_cpus["name"]
    list_cpu_ids = dict_cpus["id"]
    list_gpus = dict_gpus["name"]
    list_gpu_ids = dict_gpus["id"]
    list_fpgas = dict_fpgas["name"]
    list_fpga_ids = dict_fpgas["id"]

    dict_hostgpus, dict_hostfpgas = get_listHostsComponents(log_args=log_args)
    
    # # create dictionary with components of each host (eg., dict_hostgpus["saturn"] = ["TitanX", "Titan XP"])
    # print(list_hostscomps)
    # dict_hostgpus = {host[0]: [] for host in full_list_hosts}
    # dict_hostfpgas = {host[0]: [] for host in full_list_hosts}
    # for entry in list_hostscomps:
    #     if entry[1] == 1:
    #         dict_hostgpus[entry[0]].append(entry[2])
    #     else:
    #         dict_hostfpgas[entry[0]].append(entry[2])

    # create dictionary with usage status of each host over the next week
    dict_hosts_usage = {}
    for host in full_list_hosts:
        dict_hosts_usage[host["hostname"]] = check_hostStatusNextWeek(host["id"], log_args)

    return render_template('layouts/edit_hosts.html', hosts_usage=dict_hosts_usage, all_hostgpus=dict_hostgpus, all_hostfpgas=dict_hostfpgas, hosts=full_list_hosts, cpus=list_cpus, cpu_ids=list_cpu_ids, num_cpus=len(list_cpus), gpus=list_gpus, gpu_ids=list_gpu_ids, num_gpus=len(list_gpus), fpgas=list_fpgas, fpga_ids=list_fpga_ids, num_fpgas=len(list_fpgas))

# Enable/Disable specific Host (POST only)
@app_routes.route('/toggle_host', methods=["POST"])
@login_required
def toggle_enable_host():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    hostID = int(request.get_json().get("host_id", ""))

    update_toggleEnableHost(hostID, log_args=log_args)

    return "OK"

# Remove specific Host (POST only)
@app_routes.route('/remove_host', methods=["POST"])
@login_required
def remove_host():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    hostID = int(request.get_json().get("host_id", ""))

    del_host(hostID, log_args=log_args)
    return "OK"

# Update specific Host (change IP address or GPU/FPGA availability) (POST only)
@app_routes.route('/update_host', methods=["POST"])
@login_required
def update_host():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    args = request.get_json()

    hostID = int(args.get("id", ""))
    hostname = args.get("hostname", "")
    ipaddr = int(args.get("ip", ""))
    cpu = int(args.get("cpu", "")[0])
    gpus = args.get("gpu", "")
    fpgas = args.get("fpga", "")

    update_configHost(hostID, hostname=hostname, ip=ipaddr, cpu=cpu, gpus=gpus, fpgas=fpgas, log_args=log_args)

    return "OK"

# Add new host page (POST only)
@app_routes.route('/new_host', methods=["POST"])
@login_required
def new_host():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    full_list_hosts = get_fullListHosts(log_args=log_args)
    list_hostnames = [i["hostname"] for i in full_list_hosts]
    list_ipaddrs = [i["ip"] for i in full_list_hosts]
    # print(list_hostnames)
    # print(list_ipaddrs)

    new_host = {}
    new_host["hostname"] = request.form["hostname"]
    
    # check if hostname is already registered
    if new_host["hostname"] in list_hostnames:
        flash("ERROR: Host {} is already registered!".format(new_host["hostname"]))
        return redirect(url_for('app_routes.edit_hosts', _external=True, _scheme='https'))
    
    new_host["ip"] = request.form["ipaddr"]
    
    # check if ipaddr is already in use
    if int(new_host["ip"]) in list_ipaddrs:
        flash("ERROR: IP address X.X.X.{} is already being used!".format(new_host["ip"]))
        return redirect(url_for('app_routes.edit_hosts', _external=True, _scheme='https'))

    new_host["cpu"] = request.form["cpu"]
    
    # confirm if cpuID is valid
    dict_cpus = get_listComponents(CODE_CPU, log_args=log_args)
    list_cpu_ids = dict_cpus["id"]
    if int(new_host["cpu"]) not in list_cpu_ids:
        flash("ERROR: CPU ID is not valid!")
        return redirect(url_for('app_routes.edit_hosts', _external=True, _scheme='https'))

    form_keys = request.form.keys()
    
    # confirms if there was a GPU selected
    if "hasgpu" in form_keys:
        new_host["gpu"] = request.form.getlist("hasgpu") #needs to get the list, because there could be more than 1
        
        # confirm if all gpuIDs are valid
        dict_gpus = get_listComponents(CODE_GPU, log_args=log_args)
        list_gpu_ids = dict_gpus["id"]
        for new_host_gpu in new_host["gpu"]:
            if int(new_host_gpu) not in list_gpu_ids:
                flash( "ERROR: GPU ID is not valid!")
                return redirect(url_for('app_routes.edit_hosts', _external=True, _scheme='https'))
    else:
        new_host["gpu"] = []

    # confirms if there was an FPGA selected
    if "hasfpga" in form_keys:
        new_host["fpga"] = request.form.getlist("hasfpga")

        # confirm if all fpgaIDs are valid
        dict_fpgas = get_listComponents(CODE_FPGA, log_args=log_args)
        list_fpga_ids = dict_fpgas["id"]
        for new_host_fpga in new_host["fpga"]:
            if int(new_host_fpga) not in list_fpga_ids:
                flash("ERROR: FPGA ID is not valid!")
                return redirect(url_for('app_routes.edit_hosts', _external=True, _scheme='https'))
    else:
        new_host["fpga"] = []

    # EVERYTHING IS VALID
    insert_newEntry(Host, new_host, log_args=log_args)

    return redirect(url_for('app_routes.edit_hosts', _external=True, _scheme='https'))
