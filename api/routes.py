from flask_httpauth import HTTPBasicAuth
from flask import abort, request, jsonify, g, make_response, url_for
from flask_restful import Resource
from api.models import User
from api import cache, db

auth = HTTPBasicAuth()


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

        if len(username) < 5 or len(password) < 5:
            return make_response(jsonify({'message': 'Username and password must be more than 5 characters.'}), 400)

        if User.query.filter_by(username=username).first() is not None:
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

