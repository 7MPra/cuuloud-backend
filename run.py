from flask import render_template, send_file, redirect, url_for, request
from app import app, socketio, session
from namespace import *
from flask_session import Session
from util import url
Session(app)


@app.route('/')
def index():
    '''
    サイト表示用
    IPアドレスも同時に記録するように設計
    '''
    session['ip'] = request.headers.get('X-Forwarded-For', request.remote_addr)
    return render_template('index.html')


@app.route('/verify/<id>')
def verify(id):
    '''
    URL認証用
    セッションに任意のIDが付与されてからメインページにリダイレクトされる
    '''
    session['verify'] = id
    return redirect(url.url)


@app.route('/favicon.ico')
def favicon():
    '''
    favicon送信用
    本番環境ではnginxとかに任せるので開発時用
    '''
    return send_file('../dist/favicon.png')

#ソケットの名前空間
socketio.on_namespace(auth.AuthNameSpace('/auth'))
socketio.on_namespace(room.RoomNameSpace('/room'))
