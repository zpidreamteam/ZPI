import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'zpi.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

MAX_SEARCH_RESULTS = 50

APP_PATH = '/app'
UPLOADS_BOOKS_IMAGES = '/static/img/books/'
UPLOADS_FOLDER = os.path.realpath('.') + APP_PATH + UPLOADS_BOOKS_IMAGES
DEFAULT_FILE_STORAGE = 'filesystem'
FILE_SYSTEM_STORAGE_FILE_VIEW = 'static'