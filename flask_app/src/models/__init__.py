import sys
import logging
from sqlalchemy import inspect

from flask_app.app import db
from flask_app.src.ldap_auth import user_try_login
from flask_app.src.global_stuff import DEBUG_MODE


# Global Variables
SQLITE          = 'sqlite'

# Table Names
USER            = 'user'
COMPONENT       = 'component'
HOST            = 'host'
HOSTCOMPONENT   = 'hostcomponent'
RESTYPE         = 'reservation_type'
RESERVATION     = 'reservation'

# Components type coders
CODE_CPU        = 0
CODE_GPU        = 1
CODE_FPGA       = 2

SQLITE_LEVEL_NUM = 25
if not DEBUG_MODE:
    # Create custom logging level for SQLITE accesses
    logging.addLevelName(SQLITE_LEVEL_NUM, "SQLITE")
    def infosql(self, message, *args, **kws):
        if self.isEnabledFor(SQLITE_LEVEL_NUM):
            self._log(SQLITE_LEVEL_NUM, message, args, **kws) 
    logging.Logger.infosql = infosql


# Model class for the Users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    super_user = db.Column(db.Integer)

    user_reservations = db.relationship("Reservation", backref="reservation_user", lazy="dynamic")

    def __init__(self, args):
        self.username = args["username"]
        self.super_user = args["super_user"]

    def __repr__(self):
        return '<User {}>'.format(self.username)    

    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

    # LDAP LOGIN STUFF
    @staticmethod
    def try_login(username, password):
        return user_try_login(username, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)




# Helper table to create the many-to-many relationship between Components (GPUs, FPGAS) and Hosts
HostComponent = db.Table("hostcomponent", 
    db.Column("hostID", db.Integer, db.ForeignKey("host.id"), primary_key=True),
    db.Column("componentID", db.Integer, db.ForeignKey("component.id"), primary_key=True)
    )

# Model class for the Hosts
class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(64), index=True, unique=True) 
    ip = db.Column(db.Integer, unique=True, nullable=False)
    cpu = db.Column(db.Integer, db.ForeignKey("component.id"))
    enabled = db.Column(db.Integer, nullable=False)

    # not and actual field in the table
    components = db.relationship("Component", secondary=HostComponent, lazy="dynamic", backref=db.backref("assigned_to", lazy=True))
    host_reservations = db.relationship("Reservation", backref="reservation_host", lazy="dynamic")

    def __init__(self, args):
        self.hostname = args["hostname"]
        self.ip = args["ip"]
        self.cpu = args["cpu"]
        self.enabled = 1

    def __repr__(self):
        return '<Host {}>'.format(self.hostname)
    
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

# Model class for the Components (CPUs, GPUs or FPGAs)
class Component(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer, nullable=False) # component.type: 0-CPU; 1-GPU; 2-FPGA
    name = db.Column(db.String(64), nullable=False) # component/device name
    generation = db.Column(db.String(20)) # device family (eg., Haswell (cpu), Skylake (cpu), Volta (gpu), etc)
    manufacturer = db.Column(db.String(20)) # Manufacturer (eg., Intel, AMD, NVIDIA, Xilinx, etc.)
    
    # not and actual field in the table
    hosts = db.relationship("Host", backref="host_cpu", lazy="dynamic")
    
    def __init__(self, args):
        self.name = args["name"]
        self.type = args["type"]
        self.generation = args["generation"]
        self.manufacturer = args["manufacturer"]

    def __repr__(self):
        return '<Component {}>'.format(self.name)  

    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

# Model class for the Reservation Types
class Reservation_type(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    
    type_reservations = db.relationship("Reservation", backref="reservation_restype", lazy="dynamic")
    
    def __init__(self, args):
        self.name = args["name"]
        self.description = args["description"]

    def __repr__(self):
        return '<ReservationType {}>'.format(self.name)  
    
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

# Model class for the Reservations
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    userID = db.Column(db.Integer, db.ForeignKey("user.id"))
    hostID = db.Column(db.Integer, db.ForeignKey('host.id'))
    reservation_type = db.Column(db.Integer, db.ForeignKey("reservation_type.id"))

    begin_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))

    def __init__(self, args):
        self.userID = args["userID"]
        self.hostID = args["hostID"]
        self.reservation_type = args["reservation_type"]
        self.begin_date = args["begin_date"]
        self.end_date = args["end_date"]

    def __repr__(self):
        return '<Reservation {}>'.format(self.id) 

    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs} 

from . import sql_query, sql_insert, sql_update, sql_delete, aux_checks