import os.path
import smtplib
from email import message
from email.utils import formatdate
from config import conf

def send(email: str, subject: str, text: str):
    '''
    メールを送信
    宛先と題名、テキストを指定する。
    SMTPなどの設定はconfig.yamlから設定される。
    '''
    s = smtplib.SMTP_SSL(conf.smtp.get('host'), conf.smtp.get('port'))
    s.login(conf.smtp.get('user'), conf.smtp.get('pass'))
    msg = message.EmailMessage()
    msg.set_content(text)
    msg['Subject'] = subject
    msg['From'] = conf.smtp.get('address')
    msg['Date'] = formatdate()
    msg['To'] = email
    s.send_message(msg)
    s.quit()

def send_template(email: str, subject: str, template_name: str, *args, **kwargs):
    '''
    テンプレートを利用したメールの送信
    宛先と題名、テンプレの名前とテンプレの引数を指定する。
    テンプレートの中身は同ディレクトリ内にhtmlファイルとして保存されている。
    SMTPなどの設定はconfig.yamlから設定される。
    '''
    with open(os.path.join(os.path.dirname(__file__), f'{template_name}.html'),'r', encoding='utf-8') as f:
        text = f.read()
        text = text.format(**kwargs)
    send(email, subject, text)
