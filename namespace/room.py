from flask_socketio import Namespace, emit, join_room, leave_room, close_room, rooms, disconnect
from util import randomstr, crypt
from config import conf
from engine import db
from model import Room, RoomSchema, Join, User, Invite
from app import app, session
from flask_session import Session
import datetime
Session(app)

'''
部屋やチャットに関する動作を扱う名前空間を定義
'''

class RoomNameSpace(Namespace):
    def on_connect(self):
        '''
        接続時の動作を定義
        '''
        #ログインしてるかチェック
        if session.get('login'):
            return
        #アクセスしたユーザーが参加している部屋をDBから取得
        my_join_data = Join.query.filter(
            Join.user_id == session.get('id')).all()
        for r in my_join_data:
            join_room(r.room_id)
        room_schema = RoomSchema(many=False)
        my_join_rooms = [room_schema.dump(Room.query.filter(
            Room.id == r.room_id).first()) for r in my_join_data]
        #DBから取得して作ったデータをjoinned_roomsイベントにぶん投げる
        emit('joinned_rooms', my_join_rooms)
        room_schema = RoomSchema(many=True)
        #部屋一覧も取得してroomsイベントにぶん投げる
        emit('rooms', room_schema.dump(Room.query.all()))

    def on_disconnect(self):
        '''
        切断時の動作を定義
        '''
        #ログインしてるかチェック
        if session.get('login'):
            return
        #参加していた部屋の取得
        my_join = Join.query.filter(Join.user_id == session.get('id')).all()
        if not my_join:
            return
        for join in my_join:
            #TODO:ここから切断通知を出せるようにしとく
            leave_room(join.room_id)

    def on_get_all_rooms(self):
        '''
        すべての部屋を取得する動作を定義
        '''
        #ログインしてなかったら弾く
        if not session.get('login'):
            emit('notice', {'message': 'ログインが必要です'})
            return
        #すべてDBからとってきてぶん投げる
        room_schema = RoomSchema(many=True)
        emit('rooms', room_schema.dump(Room.query.all()))
        #自分の参加している部屋たちをDBからとってきて投げる
        my_join_data = Join.query.filter(
            Join.user_id == session.get('id')).all()
        for r in my_join_data:
            join_room(r.room_id)
        room_schema = RoomSchema(many=False)
        my_join_rooms = [room_schema.dump(Room.query.filter(
            Room.id == r.room_id).first()) for r in my_join_data]
        emit('joinned_rooms', my_join_rooms)

    def on_create_room(self, payload):
        '''
        部屋を作成する動作を定義
        '''
        #ログインしてなかったら弾く
        if not session.get('login'):
            emit('notice', {'message': 'ログインが必要です。'})
            return
        #部屋の名前が空白だったら弾く
        if not payload.get('name').split():
            emit('notice', {'message': '部屋の名前を入力してください。'})
            return
        #最後に部屋を作った日時を確認
        before_created = Room.query.filter(
            Room.host_id == session.get('id')).first()
        #config.yamlで設定された分数経ってるかチェックする
        if before_created:
            limit = datetime.timedelta(
                minutes=conf.app.get('lim_min_createroom'))
            if datetime.datetime.now() - before_created.created_at < limit:
                emit('notice', {
                     'message': f'''一度にたくさんの部屋は作れません。
                     あと{round(((limit - (datetime.datetime.now() - before_created.created_at)).seconds)/60)}分ほどお待ちください。'''})
                return
            else:
                del limit, before_created
        #部屋のID生成
        room = randomstr.randomstr(20)
        #申し訳程度の衝突防止
        while Room.query.filter(Room.id == room).first():
            room = randomstr.randomstr(20)
        #ユーザーの情報をDBからとってくる
        me = User.query.filter(User.id == session.get('id')).first()
        #部屋のデータと部屋の作成者の参加データをDBに書き込む
        new_room = Room(id=room, name=payload.get('name'),
                        host_id=session.get('id'), host_name=me.name)
        new_join = Join(user_id=session.get('id'), room_id=room)
        db.session.add(new_room)
        db.session.add(new_join)
        db.session.commit()
        join_room(room)
        emit('join', {'user_id': session.get('id'), 'text': None, 'user_name': me.name,
             'created_at': datetime.datetime.now().isoformat(), 'room_id': room}, room=room)
        #参加した部屋一覧を更新
        my_join_data = Join.query.filter(
            Join.user_id == session.get('id')).all()
        room_schema = RoomSchema(many=False)
        my_join_rooms = [room_schema.dump(Room.query.filter(
            Room.id == r.room_id).first()) for r in my_join_data]
        emit('joinned_rooms', my_join_rooms)
        #部屋一覧の更新
        room_schema = RoomSchema(many=True)
        emit('rooms', room_schema.dump(Room.query.all()), broadcast=True)

    def on_join_room(self, payload):
        '''
        部屋に参加する動作を定義
        '''
        #ログインしてなかったら弾く
        if not session.get('login'):
            emit('notice', {'message': 'ログインが必要です。'})
            return
        room = payload.get('room')
        #部屋のデータをDBからとってくる
        target = Room.query.filter(Room.id == room).first()
        #本当に存在するのか確認
        if not target:
            emit('notice', {'message': 'この部屋は存在しません。'})
            room_schema = RoomSchema(many=True)
            emit('rooms', room_schema.dump(Room.query.all()), broadcast=True)
            return
        #DBに自分の参加データがすでにあるのか確認
        my_join = Join.query.filter(Join.user_id == session.get(
            'id'), Join.room_id == room).first()
        #存在してたら撤退
        if my_join:
            return
        #DBに自分の参加データを書き込み、socket.ioの参加処理も行う
        new_join = Join(user_id=session.get('id'), room_id=room)
        db.session.add(new_join)
        join_room(room)
        db.session.commit()
        #参加データの更新
        my_join_data = Join.query.filter(
            Join.user_id == session.get('id')).all()
        room_schema = RoomSchema(many=False)
        my_join_rooms = [room_schema.dump(Room.query.filter(
            Room.id == r.room_id).first()) for r in my_join_data]
        emit('joinned_rooms', my_join_rooms)
        #部屋のユーザーたちに参加通知
        emit('join', {'room_id': room, 'created_at': datetime.datetime.now().isoformat(), 'text': None, 'user_id': session.get('id'), 'user_name': User.query.filter(
            User.id == session.get('id')).first().name}, room=room)

    def on_leave_room(self, payload):
        '''
        部屋から退出する動作を定義
        '''
        #ログインしてないなら弾く
        if not session.get('login'):
            emit('notice', {'message': 'ログインが必要です。'})
            return
        room = payload.get('room')
        #参加データをDBからとってくる
        my_join = Join.query.filter(Join.user_id == session.get(
            'id'), Join.room_id == room).first()
        #本当に存在するのか確認
        if not my_join:
            emit('notice', {'message': 'この部屋に参加してません。'})
            return
        #DBから削除して、socket.ioの退出処理も行う
        db.session.delete(my_join)
        leave_room(room)
        emit('leave', {'room_id': room, 'created_at': datetime.datetime.now().isoformat(), 'text': None, 'user_id': session.get('id'), 'user_name': User.query.filter(
            User.id == session.get('id')).first().name}, room=room)
        db.session.commit()
        #参加データを更新
        my_join_data = Join.query.filter(
            Join.user_id == session.get('id')).all()
        room_schema = RoomSchema(many=False)
        my_join_rooms = [room_schema.dump(Room.query.filter(
            Room.id == r.room_id).first()) for r in my_join_data]
        emit('joinned_rooms', my_join_rooms)
        #退出した部屋が無人ならその部屋を削除
        joinned_member = Join.query.filter(Join.room_id == room).first()
        if not joinned_member:
            db.session.delete(Room.query.filter(Room.id == room).first())
            db.session.commit()
            room_schema = RoomSchema(many=True)
            emit('rooms', room_schema.dump(Room.query.all()), broadcast=True)

    def on_message(self, payload):
        '''
        メッセージ送信の動作を定義
        '''
        #空白を弾く
        if not payload.get('text').split():
            emit('notice', {'message': '発言を入力してください。'})
            return
        #メッセージとして送信
        emit('message', {'text': payload.get('text'), 'room_id': payload.get(
            "id"), 'created_at': datetime.datetime.now().isoformat(), 'user_id': session.get('id'), 'user_name': User.query.filter(User.id == session.get('id')).first().name}, room=payload.get('id'))
