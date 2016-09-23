import os
_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

SQLALCHEMY_DATABASE_PATH = os.path.join(_basedir, 'app.db')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_PATH
SQLALCHEMY_TRACK_MODIFICATIONS = False
