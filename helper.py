from flask import session, abort

def require_login():
    if "uid" not in session:
        abort(403)

def author_check(target):
    require_login()
    if session["uid"] != target["uid"]:
        return abort(403)