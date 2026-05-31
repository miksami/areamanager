from flask import Flask
from flask import redirect, render_template, request, session, abort, make_response
import sqlite3
import db
import config
import helper
import areas
import users
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return "Your passwords do not match.", 400
        passhash = generate_password_hash(password1)

        try:
            sql = "INSERT INTO users (username, passhash) VALUES (?, ?)"
            db.execute(sql, [username, passhash])
        except sqlite3.IntegrityError:
            return "Your chosen username is unavailable.", 400

        return render_template("register_ok.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        sql = "SELECT id, passhash FROM users WHERE username = ?"
        query = db.query(sql, [username])
        if query and check_password_hash(query[0]["passhash"], password):
            session["uid"] = query[0]["id"]
            session["username"] = username
            return redirect("/")
        else:
            return "Username or password is incorrect.", 400

@app.route("/logout")
def logout():
    del session["uid"], session["username"]
    return redirect("/")

@app.route("/user/<int:uid>")
def user(uid):
    user = users.get_user(uid)
    if not user:
        abort(404)
    sql = "SELECT a.id id, a.name name, u.username author FROM areas a, users u WHERE a.uid = u.id AND u.id = ?"
    areas = db.query(sql, [uid])
    return render_template("user.html", user=user, area_count=len(areas), areas=areas)

@app.route("/new_area")
def new_area():
    return render_template("new_area.html")

@app.route("/create_area", methods=["POST"])
def create_area():
    helper.require_login()
    name = request.form["name"]
    description = request.form["description"]
    image = request.files["image"]
    if not name or not description or not image:
        return "Form is missing fields.", 400
    
    if image.mimetype != "image/jpeg":
        return "File is not a JPEG image.", 400
    file = image.read()
    if len(file) > 1024 * 1024:
        return "File is over 1 MB.", 400

    sql = "INSERT INTO areas (uid, name, description, image) VALUES (?, ?, ?, ?)"
    db.execute(sql, [session["uid"], name, description, file])
    return redirect("/area/"+str(db.last_insert_id()))

@app.route("/areas")
def list_areas():
    keyword = request.args.get("keyword") or ""
    restrict = request.args.get("restrict") or ""
    query = None
    if keyword:
        word = "%"+keyword+"%"
        if restrict == "name":
            sql = "SELECT a.id id, a.uid uid, a.name name, u.username author FROM areas a, users u WHERE a.uid = u.id AND (a.name LIKE ?)"
            query = db.query(sql, [word])
        elif restrict == "description":
            sql = "SELECT a.id id, a.uid uid, a.name name, u.username author FROM areas a, users u WHERE a.uid = u.id AND (a.description LIKE ?)"
            query = db.query(sql, [word])
        elif restrict == "author":
            sql = "SELECT a.id id, a.uid uid, a.name name, u.username author FROM areas a, users u WHERE a.uid = u.id AND (u.username LIKE ?)"
            query = db.query(sql, [word])
        else:
            sql = "SELECT a.id id, a.uid uid, a.name name, u.username author FROM areas a, users u WHERE a.uid = u.id AND (a.name LIKE ? OR a.description LIKE ?)"
            query = db.query(sql, [word, word])
    else:
        sql = "SELECT a.id id, a.uid uid, a.name name, u.username author FROM areas a, users u WHERE a.uid = u.id"
        query = db.query(sql)
    return render_template("areas.html", areas=query, keyword=keyword, restrict=restrict)

@app.route("/area/<int:aid>")
def area(aid):
    query = areas.get_area(aid)
    if not query:
        abort(404)
    return render_template("area.html", id=aid, area=query)

@app.route("/area/<int:aid>/edit", methods=["GET", "POST"])
def area_edit(aid):
    if request.method == "GET":
        query = areas.get_area(aid)
        if not query:
            abort(404)
        return render_template("edit_area.html", id=aid, area=query)
    elif request.method == "POST":
        sql = "SELECT uid FROM areas WHERE id = ?"
        query = db.query(sql, [aid])
        if not query:
            abort(404)
        helper.author_check(query[0])

        name = request.form["name"]
        description = request.form["description"]
        image = request.files["image"]
        if not name or not description:
            return "Form is missing fields.", 400

        if image:
            if image.mimetype != "image/jpeg":
                return "File is not a JPEG image."
            file = image.read()
            if len(file) > 1024 * 1024:
                return "File is over 1 MB.", 400

            sql = "UPDATE areas SET (name, description, image) = (?, ?, ?) WHERE id = ?"
            db.execute(sql, [name, description, file, aid])
        else:
            sql = "UPDATE areas SET (name, description) = (?, ?) WHERE id = ?"
            db.execute(sql, [name, description, aid])
        return redirect("/area/"+str(aid))

@app.route("/area/<int:aid>/delete", methods=["GET", "POST"])
def area_delete(aid):
    if request.method == "GET":
        sql = "SELECT uid, name FROM areas WHERE id = ?"
        query = db.query(sql, [aid])
        if not query:
            abort(404)
        return render_template("delete_area.html", id=aid, area=query[0])
    elif request.method == "POST":
        if "confirm" in request.form:
            sql = "SELECT uid FROM areas WHERE id = ?"
            query = db.query(sql, [aid])
            if not query:
                abort(404)
            helper.author_check(query[0])
            sql = "DELETE FROM areas WHERE id = ?"
            db.execute(sql, [aid])
            return redirect("/")
        else:
            return redirect("/area/"+str(aid))
        

@app.route("/area/<int:aid>/image")
def area_image(aid):
    sql = "SELECT image FROM areas WHERE id = ?"
    query = db.query(sql, [aid])
    if not query:
        abort(404)

    response = make_response(bytes(query[0][0]))
    response.headers.set("Content-Type", "image/jpeg")
    return response
