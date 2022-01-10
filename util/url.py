from config import conf
'''
url.domain:config.yamlで設定されたドメインを利用
url.url:config.yamlでの設定を利用してURLの生成
'''
domain = conf.web.get('domain')
if conf.web.get('ssl'):
    url = f'https://{domain}/'
else:
    url = f'http://{domain}/'
