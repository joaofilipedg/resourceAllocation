from flask import render_template, request, redirect, url_for, current_app
from flask_login import current_user, login_required
from datetime import datetime

# from flask_app.src.sql_sqlalchemy import dbmain, CODE_CPU, CODE_GPU, CODE_FPGA

from flask_app.src.models import *
from flask_app.src.models.sql_query import get_listComponents, get_fullListComponents
from flask_app.src.models.sql_insert import insert_newEntry
from flask_app.src.models.sql_update import update_configComponent
from flask_app.src.models.sql_delete import del_component

from . import app_routes

# Edit page, to edit list of hosts, add new host,
@app_routes.route('/edit_components')
@login_required
def edit_components():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    list_cpus = get_fullListComponents(CODE_CPU, log_args=log_args)
    list_gpus = get_fullListComponents(CODE_GPU, log_args=log_args)
    list_fpgas = get_fullListComponents(CODE_FPGA, log_args=log_args)
    print(list_cpus)

    return render_template('layouts/edit_components.html', cpus=list_cpus, num_cpus=len(list_cpus), gpus=list_gpus, num_gpus=len(list_gpus), fpgas=list_fpgas, num_fpgas=len(list_fpgas))

# Add new component page (POST only)
@app_routes.route('/new_component', methods=["POST"])
@login_required
def new_component():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    dict_all_components = get_listComponents(log_args=log_args)
    list_all_components = dict_all_components["name"]
        
    print(list_all_components)

    new_comp = {}

    # check if component with the same name is already registered
    new_comp["name"] = request.form["compname"]
    if new_comp["name"] in list_all_components:
        flash("ERROR: Component {} is already registered!".format(new_comp["name"]))
        return redirect(url_for('app_routes.edit_components', _external=True, _scheme='https'))

    new_comp["type"] = request.form["comptype"]
    new_comp["manufacturer"] = request.form["compbrand"]
    new_comp["generation"] = request.form["compgen"]

    insert_newEntry(Component, new_comp, log_args=log_args)

    return redirect(url_for('app_routes.edit_components', _external=True, _scheme='https'))

# Remove specific Component (POST only)
@app_routes.route('/remove_component', methods=["POST"])
@login_required
def remove_component():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    componentID = int(request.get_json().get("comp_id", ""))
    del_component(componentID, log_args=log_args)
    
    return "OK"

# Update specific component (change name, manufacturer or brand) (POST only)
@app_routes.route('/update_component', methods=["POST"])
@login_required
def update_component():
    username = current_user.username
    log_args = {"app": current_app, "user": username}

    args = request.get_json()
    componentID = int(args.get("id", ""))
    name = args.get("name", "")
    manufacturer = args.get("brand", "")
    gen = args.get("gen", "")

    update_configComponent(componentID, name, manufacturer, gen, log_args=log_args)

    return "OK"