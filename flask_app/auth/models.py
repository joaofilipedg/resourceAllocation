import ldap, sys, os
from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField
from wtforms.validators import InputRequired
from flask_app.app import dbldap, app


# Possible values for ldapmodule_trace_level are 
# 0 for no logging, 
# 1 for only logging the method calls with arguments, 
# 2 for logging the method calls with arguments and the complete results 
# 9 for also logging the traceback of method calls.
# WARNING: VALUES DIFFERENT THAN 0 WILL SHOW THE PASSWORDS IN CLEARTEXT
ldapmodule_trace_level = 0
ldapmodule_trace_file = sys.stderr

ldap._trace_level = ldapmodule_trace_level

# Complete path name of the file containing all trusted CA certs
# CACERTFILE='/etc/ipa/ca.crt'
CACERTFILE='/etc/ssl/certs/ca-bundle.crt'
# CACERTFILE='/etc/ssl/certs/make-dummy-cert'

def get_ldap_connection():
    conn = ldap.initialize(app.config['LDAP_PROVIDER_URL'], trace_level=ldapmodule_trace_level, trace_file=ldapmodule_trace_file)
    # Set LDAP protocol version used
    # conn.protocol_version=ldap.VERSION3
    conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)

    # Force cert validation
    conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,ldap.OPT_X_TLS_DEMAND)
    # Set path name of file containing all trusted CA certificates
    conn.set_option(ldap.OPT_X_TLS_CACERTFILE,CACERTFILE)
    
    # conn.set_option(ldap.OPT_X_TLS_DEMAND, True)
    
    # Force libldap to create a new SSL context (must be last TLS option!)
    conn.set_option(ldap.OPT_X_TLS_NEWCTX,0)

    return conn


class User(dbldap.Model):
    id = dbldap.Column(dbldap.Integer, primary_key=True)
    username = dbldap.Column(dbldap.String(100))

    def __init__(self, username):
        self.username = username

    @staticmethod
    def try_login(username, password):
        conn = get_ldap_connection()
        conn.simple_bind_s('uid=%s,cn=users,cn=accounts,dc=inesc-id,dc=pt' % username, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class LoginForm(FlaskForm):
    username = TextField('Username', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])
