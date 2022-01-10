import yaml
import os.path
with open(f'{os.path.dirname(__file__)}/config.yaml') as file:
    conf = yaml.safe_load(file)
db = conf.get('db')
web = conf.get('web')
smtp = conf.get('smtp')
redis = conf.get('redis')
app = conf.get('app')
