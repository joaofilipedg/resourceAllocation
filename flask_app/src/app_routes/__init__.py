from flask import Blueprint, url_for

app_routes = Blueprint('app_routes', __name__)

from . import login, home, reservations, hosts, components