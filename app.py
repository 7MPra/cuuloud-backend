#!/usr/bin/env python3
from model import *
from flask import Flask, session
from flask_session import Session
from engine import init_db
import logging
from config import conf
from flask_socketio import SocketIO
from gevent import monkey

async_mode = 'gevent'


def create_app():
    #Flask app
    app = Flask(__name__, static_folder='../dist/static', static_url_path='/static', template_folder='../dist')

    #Secret Key
    app.config['SECRET_KEY'] = b'you must change'
    
    #Flask Config
    app.config.from_object('engine.Config')

    #Sqlalchemy log setting
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.orm.unitofwork').setLevel(logging.DEBUG)

    #Database init
    init_db(app)

    # Flask session
    app.config['SESSION_TYPE'] = 'filesystem'

    return app


app = create_app()
if conf.redis:
    redis_host = conf.redis.get('host')
    redis_port = conf.redis.get('port')
    socketio = SocketIO(app, async_mode=async_mode, manage_session=False,
                        message_queue=f'redis://{redis_host}:{redis_port}')
else:
    socketio = SocketIO(app, async_mode=async_mode, manage_session=False)

#gevent
monkey.patch_all()
