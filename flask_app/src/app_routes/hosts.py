from flask import render_template, request, redirect, url_for, current_app
from flask_login import login_required
from datetime import datetime

from flask_app.src.sql_sqlalchemy import dbmain, CODE_CPU, CODE_GPU, CODE_FPGA

from . import app_routes

# Edit page, to edit list of hosts, add new host,
@app_routes.route('/edit_hosts')
@login_required
def edit_hosts():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    full_list_hosts = dbmain.get_fullListHosts(log_args=log_args)
    print(full_list_hosts)

    list_cpus, list_cpu_ids = dbmain.get_listComponents(CODE_CPU, log_args=log_args)
    list_gpus, list_gpu_ids = dbmain.get_listComponents(CODE_GPU, log_args=log_args)
    list_fpgas, list_fpga_ids = dbmain.get_listComponents(CODE_FPGA, log_args=log_args)

    list_hostscomps = dbmain.get_listHostsComponents(log_args=log_args)
    print(list_hostscomps)
    dict_hostgpus = {host[0]: [] for host in full_list_hosts}
    dict_hostfpgas = {host[0]: [] for host in full_list_hosts}
    for entry in list_hostscomps:
        if entry[1] == 1:
            dict_hostgpus[entry[0]].append(entry[2])
        else:
            dict_hostfpgas[entry[0]].append(entry[2])
    print(dict_hostgpus)
    print(dict_hostfpgas)

    return render_template('layouts/edit_hosts.html', all_hostgpus=dict_hostgpus, all_hostfpgas=dict_hostfpgas, hosts=full_list_hosts, cpus=list_cpus, cpu_ids=list_cpu_ids, num_cpus=len(list_cpus), gpus=list_gpus, gpu_ids=list_gpu_ids, num_gpus=len(list_gpus), fpgas=list_fpgas, fpga_ids=list_fpga_ids, num_fpgas=len(list_fpgas))

# Enable/Disable specific Host (POST only)
@app_routes.route('/toggle_host', methods=["POST"])
@login_required
def toggle_enable_host():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    hostname = request.get_json().get("hostname", "")
    print(hostname)

    dbmain.toggle_enableHost(hostname, log_args=log_args)
    return "OK"

# Remove specific Host (POST only)
@app_routes.route('/remove_host', methods=["POST"])
@login_required
def remove_host():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    hostname = request.get_json().get("hostname", "")
    print(hostname)

    dbmain.del_host(hostname, log_args=log_args)
    return "OK"

# Update specific Host (change IP address or GPU/FPGA availability) (POST only)
@app_routes.route('/update_host', methods=["POST"])
@login_required
def update_host():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    args = request.get_json()
    hostname = args.get("hostname", "")
    ipaddr = args.get("ip", "")
    cpu = int(args.get("cpu", "")[0])
    gpu = args.get("gpu", "")
    fpga = args.get("fpga", "")

    # TODO:
    # print(hostname)
    # print(ipaddr)
    # print(cpu)
    # print(gpu)
    # print(fpga)
    optional_comps = {"gpu": gpu, "fpga": fpga}
    print(optional_comps)
    dbmain.update_configHost(hostname=hostname, ipaddr=ipaddr, cpu=cpu, optional_comps=optional_comps, log_args=log_args)

    return "OK"

# Add new host page (POST only)
@app_routes.route('/new_host', methods=["POST"])
@login_required
def new_host():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    full_list_hosts = dbmain.get_fullListHosts(log_args=log_args)
    list_hostnames = [i[0] for i in full_list_hosts]
    list_ipaddrs = [i[1] for i in full_list_hosts]
    # print(list_hostnames)
    # print(list_ipaddrs)

    new_host = {}

    # check if hostname is already registered
    new_host["hostname"] = request.form["hostname"]
    if new_host["hostname"] in list_hostnames:
        return "ERROR: Host {} is already registered!".format(new_host["hostname"])

    
    # check if ipaddr is already in use
    new_host["ipaddr"] = request.form["ipaddr"]
    # print(type(new_host["ipaddr"]))
    if int(new_host["ipaddr"]) in list_ipaddrs:
        return "ERROR: IP address X.X.X.{} is already being used!".format(new_host["ipaddr"])


    new_host["cpu"] = request.form["cpu"]
    
    # confirm if cpuID is valid
    _, list_cpu_ids = dbmain.get_listComponents(CODE_CPU, log_args=log_args)
    # print(list_cpu_ids)

    if int(new_host["cpu"]) not in list_cpu_ids:
        return "ERROR: CPU ID is not valid!"
    
    form_keys = request.form.keys()
    
    # confirms if there was a GPU selected
    if "hasgpu" in form_keys:
        new_host["gpu"] = request.form.getlist("hasgpu") #needs to get the list, because there could be more than 1
        
        # confirm if all gpuIDs are valid
        _, list_gpu_ids = dbmain.get_listComponents(CODE_GPU, log_args=log_args)
        for new_host_gpu in new_host["gpu"]:
            if int(new_host_gpu) not in list_gpu_ids:
                return "ERROR: GPU ID is not valid!"

    if "hasfpga" in form_keys:
        new_host["fpga"] = request.form.getlist("hasfpga")

        # confirm if all fpgaIDs are valid
        _, list_fpga_ids = dbmain.get_listComponents(CODE_FPGA, log_args=log_args)
        for new_host_fpga in new_host["fpga"]:
            if int(new_host_fpga) not in list_fpga_ids:
                return "ERROR: FPGA ID is not valid!"

    print(new_host)
    
    dbmain.insert_newHost(new_host, log_args=log_args)

    return redirect(url_for('app_routes.edit_hosts'))
