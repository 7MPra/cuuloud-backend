from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from config import conf

db_user = conf.db.get('user')
db_pass = conf.db.get('pass')
db_host = conf.db.get('host')
db_name = conf.db.get('dbname')


class DevelopmentConfig():
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/gpsns'
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///culoud.db'
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True


class Config(DevelopmentConfig):
    DEBUG = False
    SQLALCHEMY_ECHO = False


db = SQLAlchemy()
ma = Marshmallow()


def init_db(app):
    db.init_app(app)
    Migrate(app, db)
    db.app = app
