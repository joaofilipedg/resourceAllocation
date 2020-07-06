from flask import render_template, request, redirect, url_for, current_app
from flask_login import login_required
from datetime import datetime

from flask_app.src.sql_sqlalchemy import dbmain, CODE_CPU, CODE_GPU, CODE_FPGA

from . import app_routes

# Edit page, to edit list of hosts, add new host,
@app_routes.route('/edit_components')
@login_required
def edit_components():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    list_cpus = dbmain.get_fullListComponents(CODE_CPU, log_args=log_args)
    list_gpus = dbmain.get_fullListComponents(CODE_GPU, log_args=log_args)
    list_fpgas = dbmain.get_fullListComponents(CODE_FPGA, log_args=log_args)
    print(list_cpus)
    return render_template('layouts/edit_components.html', cpus=list_cpus, num_cpus=len(list_cpus), gpus=list_gpus, num_gpus=len(list_gpus), fpgas=list_fpgas, num_fpgas=len(list_fpgas))

# Add new component page (POST only)
@app_routes.route('/new_component', methods=["POST"])
@login_required
def new_component():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    list_components, _ = dbmain.get_listComponents(log_args=log_args)
        
    print(list_components)

    new_comp = {}

    # check if component with the same name is already registered
    new_comp["name"] = request.form["compname"]
    if new_comp["name"] in list_components:
        return "ERROR: Component {} is already registered!".format(new_comp["name"])

    new_comp["type"] = request.form["comptype"]
    new_comp["brand"] = request.form["compbrand"]
    new_comp["gen"] = request.form["compgen"]

    dbmain.insert_newComponent(new_comp, log_args=log_args)

    return redirect(url_for('app_routes.edit_components'))

# Remove specific Component (POST only)
@app_routes.route('/remove_component', methods=["POST"])
@login_required
def remove_component():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    componentID = request.get_json().get("comp_id", "")
    dbmain.del_component(componentID, log_args=log_args)
    return "OK"

# Update specific component (change name, manufacturer or brand) (POST only)
@app_routes.route('/update_component', methods=["POST"])
@login_required
def update_component():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    args = request.get_json()
    componentID = args.get("id", "")
    name = args.get("name", "")
    brand = args.get("brand", "")
    gen = args.get("gen", "")

    dbmain.update_configComponent(componentID, name, brand, gen, log_args=log_args)

    return "OK"