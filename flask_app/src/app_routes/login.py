import logging
import ldap
from flask import render_template, request, redirect, url_for, Blueprint, g, flash, current_app
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime

from flask_app.src.global_stuff import DEBUG_MODE
from flask_app.app import login_manager, dbldap
from flask_app.src.ldap_auth import User, LoginForm
from flask_app.src.sql_sqlalchemy import dbmain

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

@app_routes.route('/')
@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('app_routes.home'))

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

        return redirect(url_for('app_routes.home'))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('layouts/login.html', form=form)

@app_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('app_routes.login'))

