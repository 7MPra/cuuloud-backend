# backend

## How to build
```
git clone https://github.com/NaiwTeam/cuuloud_backend.git
git clone https://github.com/NaiwTeam/cuuloud_frontend.git
cd cuuloud_frontend
yarn install
yarn build
```

## How to run
```
cd cuuloud_backend
sudo apt-get install libpcre3 libpcre3-dev
pip install -r requirements.txt
flask db init
flask db migrate
flask db upgrade
flask run
```
