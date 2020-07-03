import ldap
from flask import render_template, request, redirect, url_for, Blueprint, g, flash
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime

from flask_app.app import app, scheduler, login_manager, dbldap
from flask_app.auth.models import User, LoginForm
import flask_app.src.sql_sqlalchemy as mydb
from flask_app.src.sql_sqlalchemy import dbmain, CODE_CPU, CODE_GPU, CODE_FPGA

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@auth.before_request
def get_current_user():
    g.user = current_user

@auth.route('/')
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('auth.home'))

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            super_user = User.try_login(username, password)
        except ldap.INVALID_CREDENTIALS:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('layouts/login.html', form=form)

        print("login sucessfull")
        user = User.query.filter_by(username=username).first()


        if not user:
            user = User(username, super_user)
            dbldap.session.add(user)
            dbldap.session.commit()

        login_user(user)
        # flash('You have successfully logged in.', 'success')

        return redirect(url_for('auth.home'))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('layouts/login.html', form=form)

@auth.route("/home")
@login_required
def home():
    username = current_user.username
    list_res = dbmain.get_listCurrentReservations(username)
    print(list_res)
    return render_template("layouts/home.html", curr_res=list_res)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Reservations page, to add new reservations, see current reservations or cancel one active reservation
@auth.route('/reservations')
@login_required
def reservations():
    list_hosts = dbmain.get_listEnabledHosts()
    print(list_hosts)

    list_restypes, list_restypes_ids = dbmain.get_listResTypes()
    print(list_restypes)
    print(list_restypes_ids)
    
    list_freehosts = dbmain.get_listFreeHosts()
    print(list_freehosts)

    list_res = dbmain.get_listCurrentReservations()
    print(list_res)
    return render_template('layouts/reservations.html', hosts=list_hosts, num_res_types=len(list_restypes), res_types=list_restypes, res_type_ids = list_restypes_ids, free_hosts=list_freehosts, curr_res=list_res)

# Add new reservation page (POST only)
@auth.route('/new_reservation', methods=["POST"])
@login_required
def new_reservation():

    list_users = dbmain.get_listUsers()
  
    new_reservation = {}
    new_reservation["user"] = request.form["username"]
    
    # check if user already exists in the database
    if new_reservation["user"] not in list_users:
        # if not, needs to create user (this assumes the web app already authenticated the user)
        dbmain.insert_newUser(new_reservation["user"])

        # If web app is not authenticating user, it should return an error
        # return "ERROR: User '{}' does not exist!".format(new_reservation["user"])

    # Get the rest of the form fields
    new_reservation["host"] = request.form["host"]
    new_reservation["res_type"] = request.form["res_type"]
    datetimes = request.form["datetimes"]
    datetimes = datetimes.split(" - ")
    new_reservation["begin_date"] = datetimes[0]
    new_reservation["end_date"] = datetimes[1]

    # Check if end date is already past
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if new_reservation["end_date"] <= now:
        return "ERROR: Reservation end date is already in the past ({})!".format(new_reservation["end_date"])

    # Checks for conflicts (Return True if there is a conflict)
    conflict, conflict_str = mydb.check_conflictsNewReservation(new_reservation)
    if not conflict:
        # Add reservation to DB
        res_id = dbmain.insert_newReservation(new_reservation)

        # Create new trigger to end reservation at the end date
        scheduler.add_job(func=mydb.timed_removeReservation, trigger="date", run_date=new_reservation["end_date"], args=[res_id], id='j'+str(res_id), misfire_grace_time=7*24*60*60)
    
        return redirect(url_for('auth.reservations'))
    else:
        return "ERROR: {}".format(conflict_str)
        
# Cancel reservation (POST only)
@auth.route('/cancel_reservation', methods=["POST"])
@login_required
def cancel_reservation():
    res_id = request.get_json().get("res_id", "")
    print(res_id)

    mydb.manual_removeReservation(res_id)
    return "OK"

# Edit page, to edit list of hosts, add new host,
@auth.route('/edit_hosts')
@login_required
def edit_hosts():
    full_list_hosts = dbmain.get_fullListHosts()
    print(full_list_hosts)

    list_cpus, list_cpu_ids = dbmain.get_listComponents(CODE_CPU)
    list_gpus, list_gpu_ids = dbmain.get_listComponents(CODE_GPU)
    list_fpgas, list_fpga_ids = dbmain.get_listComponents(CODE_FPGA)

    list_hostscomps = dbmain.get_listHostsComponents()
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




    # list_restypes, list_restypes_ids = dbmain.get_listResTypes()
    # print(list_restypes)
    # print(list_restypes_ids)

    return render_template('layouts/edit_hosts.html', all_hostgpus=dict_hostgpus, all_hostfpgas=dict_hostfpgas, hosts=full_list_hosts, cpus=list_cpus, cpu_ids=list_cpu_ids, num_cpus=len(list_cpus), gpus=list_gpus, gpu_ids=list_gpu_ids, num_gpus=len(list_gpus), fpgas=list_fpgas, fpga_ids=list_fpga_ids, num_fpgas=len(list_fpgas))

# Enable/Disable specific Host (POST only)
@auth.route('/toggle_host', methods=["POST"])
@login_required
def toggle_enable_host():
    hostname = request.get_json().get("hostname", "")
    print(hostname)

    dbmain.toggle_enableHost(hostname)
    return "OK"

# Remove specific Host (POST only)
@auth.route('/remove_host', methods=["POST"])
@login_required
def remove_host():
    hostname = request.get_json().get("hostname", "")
    print(hostname)

    dbmain.del_host(hostname)
    return "OK"

# Update specific Host (change IP address or GPU/FPGA availability) (POST only)
@auth.route('/update_host', methods=["POST"])
@login_required
def update_host():
    args = request.get_json()
    hostname = args.get("hostname", "")
    ipaddr = args.get("ip", "")
    cpu = int(args.get("cpu", "")[0])
    gpu = args.get("gpu", "")
    fpga = args.get("fpga", "")

    # TODO:
    print(hostname)
    print(ipaddr)
    print(cpu)
    print(gpu)
    print(fpga)
    optional_comps = {"gpu": gpu, "fpga": fpga}
    print(optional_comps)
    dbmain.update_configHost(hostname=hostname, ipaddr=ipaddr, cpu=cpu, optional_comps=optional_comps)

    return "OK"

# Add new host page (POST only)
@auth.route('/new_host', methods=["POST"])
@login_required
def new_host():
    full_list_hosts = dbmain.get_fullListHosts()
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
    _, list_cpu_ids = dbmain.get_listComponents(CODE_CPU)
    print(list_cpu_ids)
    # print(new_host["cpu"])
    # print(int(new_host["cpu"]))
    if int(new_host["cpu"]) not in list_cpu_ids:
        return "ERROR: CPU ID is not valid!"
    
    form_keys = request.form.keys()
    
    # confirms if there was a GPU selected
    if "hasgpu" in form_keys:
        new_host["gpu"] = request.form.getlist("hasgpu") #needs to get the list, because there could be more than 1
        
        # confirm if all gpuIDs are valid
        _, list_gpu_ids = dbmain.get_listComponents(CODE_GPU)
        for new_host_gpu in new_host["gpu"]:
            if int(new_host_gpu) not in list_gpu_ids:
                return "ERROR: GPU ID is not valid!"

    if "hasfpga" in form_keys:
        new_host["fpga"] = request.form.getlist("hasfpga")

        # confirm if all fpgaIDs are valid
        _, list_fpga_ids = dbmain.get_listComponents(CODE_FPGA)
        for new_host_fpga in new_host["fpga"]:
            if int(new_host_fpga) not in list_fpga_ids:
                return "ERROR: FPGA ID is not valid!"

    print(new_host)
    
    dbmain.insert_newHost(new_host)

    return redirect(url_for('auth.edit_hosts'))

# Edit page, to edit list of hosts, add new host,
@auth.route('/edit_components')
@login_required
def edit_components():
    # full_list_hosts = dbmain.get_fullListHosts()
    # print(full_list_hosts)

    list_cpus = dbmain.get_fullListComponents(CODE_CPU)
    list_gpus = dbmain.get_fullListComponents(CODE_GPU)
    list_fpgas = dbmain.get_fullListComponents(CODE_FPGA)
    print(list_cpus)
    return render_template('layouts/edit_components.html', cpus=list_cpus, num_cpus=len(list_cpus), gpus=list_gpus, num_gpus=len(list_gpus), fpgas=list_fpgas, num_fpgas=len(list_fpgas))



# Add new component page (POST only)
@auth.route('/new_component', methods=["POST"])
@login_required
def new_component():
    
    list_components, _ = dbmain.get_listComponents()
        
    print(list_components)

    new_comp = {}

    # check if component with the same name is already registered
    new_comp["name"] = request.form["compname"]
    if new_comp["name"] in list_components:
        return "ERROR: Component {} is already registered!".format(new_comp["name"])

    new_comp["type"] = request.form["comptype"]
    new_comp["brand"] = request.form["compbrand"]
    new_comp["gen"] = request.form["compgen"]

    # print(new_comp)

    dbmain.insert_newComponent(new_comp)

    return redirect(url_for('auth.edit_components'))

# Remove specific Component (POST only)
@auth.route('/remove_component', methods=["POST"])
@login_required
def remove_component():
    componentID = request.get_json().get("comp_id", "")
    # print(componentID)
    dbmain.del_component(componentID)
    return "OK"

# Update specific component (change name, manufacturer or brand) (POST only)
@auth.route('/update_component', methods=["POST"])
@login_required
def update_component():
    args = request.get_json()
    componentID = args.get("id", "")
    name = args.get("name", "")
    brand = args.get("brand", "")
    gen = args.get("gen", "")

    dbmain.update_configComponent(componentID, name, brand, gen)

    return "OK"