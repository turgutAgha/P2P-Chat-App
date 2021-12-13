import os
import time
from flask import Flask, abort, request, jsonify, g, make_response, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache
from flask_restful import Resource, Api

# version = 'v1'
# MYSQL_USER = os.environ['MYSQL_USER']
# MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
# MYSQL_ROOT_HOST = os.environ['MYSQL_ROOT_HOST']
# MYSQL_DATABASE = os.environ['MYSQL_DATABASE']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'it is random string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:very_strong_password@localhost/chat_app'
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

auth = HTTPBasicAuth()


class User(db.Model):
    tablename = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expires_in=600):
        return jwt.encode(
            payload={'id': self.id, 'exp': time.time() + expires_in},
            key=app.config['SECRET_KEY'], algorithm='HS256'
        )

    @staticmethod
    def verify_auth_token(token):
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],
                              algorithms=['HS256'])
        except Exception as e:
            return e
        return User.query.get(data['id'])


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


class SignUp(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        username = json_data['username'].strip()
        password = json_data['password']
        # username = request.json.get('username')
        # password = request.json.get('password')
        if len(username) < 5 or len(password) < 5:
            # abort(400)  # missing arguments
            return make_response(jsonify({'message': 'Username and password must be more than 5 characters.'}), 400)
        if User.query.filter_by(username=username).first() is not None:
            # abort(400)  # existing user
            return make_response(jsonify({'message': 'User exists. Please, use different username.'}), 400)
        user = User(username=username)
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()
        response = make_response(jsonify({'username': user.username}), 201)
        response.headers['Location'] = url_for('get_user', id=user.id, _external=True)
        return response

class Login(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        username = json_data['username'].strip()
        password = json_data['password']
        ip_address = json_data['ip_address']
        port = json_data['port']
        
        
        if len(username) < 5 or len(password) < 5:
            return make_response(jsonify({'message': 'Username and password must be more than 5 characters.'}), 401)
        
        user = User.query.filter_by(username=username).first()
        if user is None:
            return make_response(jsonify({'message': 'User does not exist.'}), 401)
        
        if user.verify_password(password):
            key = username
            value = [ip_address, port, 'online']
            cache.set(key, value)
            return make_response(jsonify({'message' : 'You are logged in successfully.'}), 200)
        else:
            return make_response(jsonify({'message' : 'Wrong password.'}), 401)

class GetUser(Resource):
    def get(self, id):
        user = User.query.get(id)
        if not user:
            abort(400)
        return jsonify({'username': user.username})

class OnlineMembers(Resource):
    def get(self):
        members = []
        for key in cache.cache._write_client.keys():
            key = key.decode('utf-8')
            if (cache.get(key)[2] == 'online'):
                ip_address = cache.get(key)[0]
                port = cache.get(key)[1]
                members.append([key, [ip_address, port]])
        return jsonify({'members': members})

class Token(Resource):
    @auth.login_required
    def get(self):
        token = g.user.generate_auth_token(600)
        return jsonify({'token': token, 'duration': 600})




class Exit(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        username = json_data['username']
        cache.delete(username)
        return jsonify({'data': "Deletion is successful"})


api.add_resource(SignUp, '/api/register')
api.add_resource(Login, '/api/login')
api.add_resource(GetUser, '/api/users/<int:id>', endpoint='get_user')
api.add_resource(Token, '/api/token')
api.add_resource(OnlineMembers, '/api/online_members')
api.add_resource(Exit, '/api/disconnect')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)