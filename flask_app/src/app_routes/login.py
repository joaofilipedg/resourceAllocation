import logging
import ldap
from flask import render_template, request, redirect, url_for, Blueprint, g, flash, current_app, session
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime

from flask_app.src.global_stuff import DEBUG_MODE
from flask_app.app import login_manager, dbldap
from flask_app.src.ldap_auth import User, LoginForm
from flask_app.src.sql_sqlalchemy import dbmain


from . import app_routes




@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# @app_routes.before_request
# def before_request():
#     if request.url.startswith('http://'):
#         url = request.url.replace('http://', 'https://', 1)
#         code = 301
#         return redirect(url, code=code)

# @app_routes.before_request
# def make_session_permanent():
#     session.permanent = True
#     app_routes.permanent_session_lifetime = timedelta(minutes=1)

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
    print(1)
    if current_user.is_authenticated:
        print(2)
        flash('You are already logged in.')
        return redirect(url_for('app_routes.home', _external=True, _scheme='https'))
    print(3)

    # form = LoginForm(request.form)
    form = LoginForm()
    print(4)
    if form.validate_on_submit():
        print(5)
    # if request.method == 'POST' and form.validate():
        # username = request.form.get('username')
        # password = request.form.get('password')
        username = form.username.data
        password = form.password.data


        try:
            super_user = User.try_login(username, password)
            print(7)
        except ldap.INVALID_CREDENTIALS:
            print(8)
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('layouts/login.html', form=form)

        print(9)
        print("login sucessfull")
        user = User.query.filter_by(username=username).first()

        session.permanent = True # to allow for connection timeout after time defined in PERMANENT_SESSION_LIFETIME

        print(10)
        if not user:
            user = User(username, super_user)
            print(11)
            dbldap.session.add(user)
            dbldap.session.commit()

        print(12)
        # login_user(user, remember=form.remember_me.data)
        login_user(user)
        print(13)
        # flash('You have successfully logged in.', 'success')

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('app_routes.home', _external=True, _scheme='https')
        print(14)
        return redirect(next_page)

    # if form.errors:
    #     flash(form.errors, 'danger')

    print(15)
    return render_template('layouts/login.html', form=form)

@app_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('app_routes.login', _external=True, _scheme='https'))



