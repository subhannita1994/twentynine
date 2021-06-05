"""Flask configuration."""
from os import environ, path
from dotenv import load_dotenv


basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

TESTING = False
DEBUG = True
FLASK_ENV = 'development'
SECRET_KEY = environ.get('SECRET_KEY') or 'someSecretString'
SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL') or \
        'sqlite:////' + path.join(basedir, 'app.db?check_same_thread=False')
SQLALCHEMY_TRACK_MODIFICATIONS = False