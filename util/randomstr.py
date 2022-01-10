import random, string
def randomstr(n):
   '''
   ランダムな長さnの文字列を生成
   '''
   return ''.join(random.choices(string.ascii_letters + string.digits, k=n))
