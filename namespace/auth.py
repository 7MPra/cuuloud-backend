from flask_socketio import Namespace, emit, join_room, leave_room, close_room, rooms, disconnect
from util import randomstr, crypt, mail, url
from engine import db
from model import RoomSchema, Join, User, Invite, Verify, verify
from app import app, session
from flask_session import Session
Session(app)

'''
ユーザーや認証に関する動作を扱う名前空間を定義
'''

class AuthNameSpace(Namespace):
    def on_connect(self):
        '''
        接続時の動作を定義
        '''
        #メールアドレス認証の部分
        #verify/からアクセスした人にはセッションの中に認証IDがついているのでそれを読み取る
        if session.get('verify'):
            #DBとの照合をする
            verify = Verify.query.filter(
                Verify.token == session.get('verify')).first()
            if verify:
                #DBからユーザーとの照合をする
                verified_user = User.query.filter(
                    User.id == verify.user_id).first()
                #認証成功のメッセージを表示
                emit('notice', {
                     'message': 'メールアドレス認証が成功しました！ログインをして、サービスをお楽しみください！'})
                #DBに認証結果を反映
                verified_user.verified = True
                db.session.delete(verify)
                db.session.commit()
                #ログアウトさせる
                emit('login', {'login': False, 'id': None, 'name': None})
                #認証IDの中身を空っぽにする
                session['verify'] = None
            else:
                #認証IDの中身を空っぽにする
                session['verify'] = None
        #ログインしている場合の処理
        if session.get('login'):
            #ログインしているユーザーの情報をDBから取得
            target = User.query.filter(User.id == session.get('id')).first()
            #IPアドレスを記録する
            target.ip = str(session.get('ip'))
            db.session.commit()
            #ログイン情報をクライアント側に送信
            emit('login', {'login': session.get('login'),
                 'id': session.get('id'), 'name': target.name})
        else:
            #空のログイン情報をクライアント側に送信
            emit('login', {'login': False, 'id': None, 'name': None})

    def on_disconnect(self):
        pass

    def on_login(self, payload):
        '''
        ログインリクエスト時の動作を定義
        '''
        #すでにログインされてたら弾く
        if session.get('login'):
            return
        session['login'] = False
        #入力されたidに該当するデータを取得
        target = User.query.filter(User.id == payload.get('id')).first()
        #そのデータの存在の確認とともにパスワードのハッシュのチェック
        if (not target) or (not crypt.check(payload.get('password'), target.password)):
            emit('auth_error', {'message': 'IDかパスワードが間違っています。'})
            return
        #IPの記録
        target.ip = str(session.get('ip'))
        db.session.commit()
        #メルアド認証されてるか検証
        if not target.verified:
            emit('auth_error', {'message': 'メールアドレス認証が済まされていません。'})
            return
        session['id'] = payload.get('id')
        session['login'] = True
        #ログインの結果を送信
        emit('login', {'login': session.get('login'), 'id': session.get('id'), 'name':target.name})

    def on_logout(self):
        '''
        ログアウトリクエスト時の動作を定義
        '''
        #ログインされていない状況を明示的にセッションで示し、セッションからIDを取っ払って下手に悪用されないようにする
        session['id'] = None
        session['login'] = False
        emit('login', {'login': session.get('login'), 'id': session.get('id')})

    def on_apply_settings(self, payload):
        '''
        設定適用時の動作を定義
        '''
        #ログインしてなかったら弾く
        if not session.get('login'):
            emit('notice', {'message': 'ログインが必要です。'})
            return
        #自分のデータをDBからとってくる
        me = User.query.filter(User.id == session.get('id')).first()
        #名前の変更のチェック
        if payload.get('changedName') and payload.get('name').split():
            me.name = payload.get('name')
            db.session.commit()
        #設定の送信
        emit('changed_settings', {'name':me.name})
        emit('notice', {'message': '設定を適用しました。'})

    def on_invite(self, payload):
        '''
        招待時の動作を定義
        '''
        #ログインしてなかったら弾く
        if not session.get('login'):
            emit('notice', {'message': 'ログインが必要です。'})
            return
        #メールの重複を確認
        if User.query.filter(User.email == payload.get("email")).first():
            emit('notice', {'message': 'このメールアドレスはすでに登録されています。'})
            return
        if Invite.query.filter(Invite.email == payload.get('email')).first():
            emit('notice', {'message': 'このメールアドレスはすでに招待されています。'})
            return
        #メルアドの表記チェック
        email = payload.get("email") if payload.get("email") else ''
        if not (email.count('@') == 1 and email.split('@')[-1].count('.') != 0):
            emit('notice', {'message': '不正なメールアドレスです。'})
            return
        invited_person = User.query.filter(User.id == session.get('id')).first()
        #ユーザーの招待上限のチェック
        if invited_person.invitation_times_limit <= 0:
            emit('notice', {'message': '招待可能回数を超過しました。'})
            return
        #招待データの作成
        invited_person.invitation_times_limit -= 1
        new = Invite(user_id=session.get('id'), email=email)
        db.session.add(new)
        db.session.commit()
        #メール送信
        me = User.query.filter(User.id == session.get('id')).first()
        mail.send_template(payload.get(
            'email'), f'{me.name}からCuuloudへの招待が届きました！', 'invite', url=url.url, name=me.name)
        emit('notice', {'message': '招待が完了しました。'})

    def on_register(self, payload):
        '''
        登録時の動作を定義
        '''
        #ACII文字以外のIDを弾く
        if not payload.get('id').isascii():
            emit('auth_error', {'message': 'IDにはASCII文字しか使えません。'})
            return
        #IDの重複を弾く
        if User.query.filter(User.id == payload.get('id')).first():
            emit('auth_error', {'message': '登録しようとしているIDがすでに存在します。'})
            return
        #メルアドの重複を弾く
        if User.query.filter(User.email == payload.get("email")).first():
            emit('auth_error', {'message': 'このメールアドレスはすでに登録されています。'})
            return
        #招待されていないなら弾く
        target = Invite.query.filter(Invite.email == payload.get("email")).first()
        if not target:
            emit('auth_error', {'message': 'あなたは招待されていません。'})
            return
        #クソ長ネームを弾く
        if len(payload.get('name')) > 10:
            emit('auth_error', {'message': '名前が長すぎます。'})
            return
        #IDが長くてもダメ
        if len(payload.get('id')) > 15:
            emit('auth_error', {'message': 'IDが長すぎます。'})
            return
        #パスワードのハッシュの生成
        password = crypt.hash(payload.get("password"))
        #新しいユーザーデータの作成
        new = User(id=payload.get('id'), name=payload.get("name"), email=payload.get("email"), password=password, verified=False)
        #メルアド認証用IDの生成
        verify_token = randomstr.randomstr(10)
        #申し訳程度の衝突防止
        while Verify.query.filter(Verify.token == verify).first():
            verify_token = randomstr.randomstr(10)
        new_verify = Verify(token=verify_token, user_id=payload.get('id'))
        db.session.delete(target)
        db.session.add(new)
        db.session.add(new_verify)
        session['id'] = payload.get('id')
        db.session.commit()
        emit('auth_error', {'message': '登録されたメールアドレスから認証してください。'})
        #メール送信
        mail.send_template(payload.get('email'), 'Cuuloud　メール認証の確認', 'register', url=url.url, verify_token=verify_token)
