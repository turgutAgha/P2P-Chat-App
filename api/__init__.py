import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_caching import Cache

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)

cache = Cache(app, config = {
    'CACHE_TYPE': 'redis',
    'CACHE_KEY_PREFIX': '',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': '6379',
    'CACHE_REDIS_URL': 'redis://localhost:6379',
    'CACHE_DEFAULT_TIMEOUT': 0
})

from .routes import SignUp, Login, GetUser, Token, OnlineMembers, Exit

api.add_resource(SignUp, '/api/register')
api.add_resource(Login, '/api/login')
api.add_resource(GetUser, '/api/users/<int:id>', endpoint='get_user')
api.add_resource(Token, '/api/token')
api.add_resource(OnlineMembers, '/api/online_members')
api.add_resource(Exit, '/api/disconnect')