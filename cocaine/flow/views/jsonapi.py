from flask import request, render_template, session, flash, redirect, url_for, current_app, json, jsonify

from common import send_json_rpc, token_required, token_required_json, uniform, logged_in, logged_in_json
from storages.exceptions import UserExists
from cocaine.flow.storages import storage

# JSON API
def get_apps():
    try:
        mm = storage.read_manifests()
        return json.dumps([k for k in mm.iterkeys()])
    except RuntimeError:
        return jsonify([])

def get_hosts():
    return json.dumps(storage.read_hosts())

def get_runlists():
    try:
        return json.dumps(storage.read(storage.key("system", "list:runlists")))
    except RuntimeError:
        return json.dumps([])

def get_runlists_apps():
    return json.dumps(storage.read_runlists())
# 

def auth():
    username = request.values.get('username')
    password = request.values.get('password')
    user = storage.find_user_by_username(username)
    if user is None:
        return jsonify({"reason" :'Username is invalid', "result" : "fail"})

    if user['password'] != hashlib.sha1(password).hexdigest():
        return jsonify({"reason" :'Password is invalid', "result" : "fail"})

    token = user.get('token')
    if token is None:
        return jsonify({"reason" : 'Token is not set for user', "result" : "fail"})
    session['logged_in'] = token
    return jsonify({"result" : "ok", "token":token, "login" : username, "ACL" : {}})

@token_required_json(admin=False)
def userinfo(user):
    print user
    return jsonify({"result" : "ok", "ACL" : {}, "login" : storage.get_username_by_token(user.get('token'))})


def register_json():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return jsonify({"error" :'Username/password cannot be empty', "result" : 400})

        try:
            create_user(username, password)
        except UserExists:
            return jsonify({"error" :'Username is not available', "result" : 400})
        try:
            user = storage.find_user_by_username(username)
        except Exception:
            return jsonify({"result" : 500, "error" : "Unknown register error"})
        res = { "result" : 200, "login" : username }
        user.pop("password")
        res.update(user)
        return jsonify(res)

@logged_in_json
def logout_json(user):
    session.pop("logged_in", None)
    return jsonify({"result" : "ok"})
