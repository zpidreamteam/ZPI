import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_principal import ActionNeed, AnonymousIdentity, Identity, identity_changed, identity_loaded, Permission, Principal, RoleNeed
from flask.ext.uploads import init
from flask.ext.storage import get_default_storage_class
from flask import Flask
from flask.ext.mail import Mail

app = Flask(__name__)
app.config.from_object('config')

# database
db = SQLAlchemy(app)

# login manager
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

principals = Principal(app, skip_static=True)

#Needs
be_admin = RoleNeed('admin')
be_user  = RoleNeed('user')

#Permissions
admin_permission = Permission(be_admin)
admin_permission.description = "Admin's permissions"
user_perrmission = Permission(be_user)
user_perrmission.description = "User's permissions"

apps_needs = [be_admin, be_user]
apps_permissions = [admin_permission, user_perrmission]

# mail
app.config.update(
	DEBUG=False,
	#EMAIL SETTINGS
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = 'no.reply.bookstree@gmail.com',
	MAIL_PASSWORD = 'ZPIdream')
mail = Mail()
mail.init_app(app)

# storage
Storage = get_default_storage_class(app)
init(db, Storage)

from app import views, models, admin_panel
