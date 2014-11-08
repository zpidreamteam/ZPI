import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.uploads import init
from flask.ext.storage import get_default_storage_class
from flask import Flask
from flask.ext.mail import Mail

app = Flask(__name__)
app.config.from_object('config')

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

init(db, get_default_storage_class(app))
app.config.update(
	DEBUG=False,
	#EMAIL SETTINGS
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = 'no.reply.bookstree@gmail.com',
	MAIL_PASSWORD = 'ZPIdream'
	)
mail = Mail()
mail.init_app(app)

db = SQLAlchemy(app)
Storage = get_default_storage_class(app)
init(db, Storage)

from app import views, models


