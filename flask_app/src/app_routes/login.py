import logging
import ldap
from flask import render_template, request, redirect, url_for, Blueprint, g, flash, current_app, session
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime

from flask_app.src.global_stuff import DEBUG_MODE
from flask_app.app import login_manager, db
from flask_app.src.ldap_auth import LoginForm
from flask_app.src.models import *
from flask_app.src.models.sql_insert import insert_newEntry
from flask_app.src.models.sql_query import get_fullTable

from . import app_routes


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app_routes.before_request
def get_current_user():
    g.user = current_user

@app_routes.after_request
def after_request(response):
    if not DEBUG_MODE:
        """ Logging after every request. """
        logger = logging.getLogger("app.access")
        logger.info(
            "%s [%s] %s %s %s %s %s %s %s",
            request.remote_addr,
            datetime.utcnow().strftime("%d/%b/%Y:%H:%M:%S.%f")[:-3],
            request.method,
            request.path,
            request.scheme,
            response.status,
            response.content_length,
            request.referrer,
            request.user_agent,
        )
    return response

@app_routes.errorhandler(404)
@app_routes.errorhandler(405)
def page_not_found(e):
    return render_template('layouts/404.html')

@app_routes.route('/', methods=['GET', 'POST'])
@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'success')
        return redirect(url_for('app_routes.home', _external=True, _scheme='https'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        log_args = {"app": current_app, "user": username}

        try:
            super_user = User.try_login(username, password)
        except ldap.INVALID_CREDENTIALS:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('layouts/login.html', form=form)

        if not DEBUG_MODE:
            logging.info("Log in by user '{}'".format(username))
        else:
            print("Log in by user '{}'".format(username))

        user = get_fullTable(User, filter_col="username", filter_value=username, return_obj=True, log_args=log_args)

        session.permanent = True # to allow for connection timeout after time defined in PERMANENT_SESSION_LIFETIME

        if not user:
            user = insert_newEntry(User, {"username":username, "super_user":super_user}, log_args=log_args)
        else: 
            user = user[0]

        login_user(user)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('app_routes.home', _external=True, _scheme='https')

        return redirect(next_page)

    return render_template('layouts/login.html', form=form)

@app_routes.route('/logout')
@login_required
def logout():
    if not DEBUG_MODE:
        logging.info("Log out by user '{}'".format(current_user.username))
    else:
        print("Log out by user '{}'".format(current_user.username))
        
    logout_user()
    return redirect(url_for('app_routes.login', _external=True, _scheme='https'))



