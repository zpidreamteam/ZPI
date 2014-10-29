import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_principal import ActionNeed, AnonymousIdentity, Identity, identity_changed, identity_loaded, Permission, Principal, RoleNeed

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

principals = Principal(app, skip_static=True)

#Needs
be_admin = RoleNeed('admin')

#Permissions
admin_permission = Permission(be_admin)
admin_permission.description = "Admin's permissions"

apps_needs = [be_admin]
apps_permissions = [admin_permission]

from app import views, models, admin_panel

