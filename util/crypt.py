import bcrypt


def hash(password: str):
    '''
    入力されたテキストのハッシュを生成（パスワード用）
    '''
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=16)).decode()


def check(password: str, hashed_password: str):
    '''
    入力されたテキストとハッシュの照合（パスワード用）
    '''
    return bcrypt.checkpw(password.encode(), hashed_password.encode())
