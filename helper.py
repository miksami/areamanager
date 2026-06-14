from flask import request, session, abort

def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

def require_login():
    if "uid" not in session:
        abort(403)

def author_check(target):
    require_login()
    if session["uid"] != target["uid"]:
        return abort(403)