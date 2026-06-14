from flask import Flask
from flask import redirect, render_template, request, session, abort, make_response
import sqlite3
import db
import config
import helper
import areas
import items
import users
import secrets
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
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        if not username or len(username) > 16:
            return "Username can't be empty or over 16 characters."
        if not password1:
            return "Password can't be empty."
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
        username = request.form.get("username")
        password = request.form.get("password")

        sql = "SELECT id, passhash FROM users WHERE username = ?"
        query = db.query(sql, [username])
        if query and check_password_hash(query[0]["passhash"], password):
            session["uid"] = query[0]["id"]
            session["username"] = username
            session["csrf_token"] = secrets.token_hex(16)
            return redirect("/")
        else:
            return "Username or password is incorrect.", 400

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/user/<int:uid>")
def user(uid):
    user = users.get_user(uid)
    if not user:
        abort(404)
    sql = "SELECT a.id id, a.name name, u.username author FROM areas a, users u WHERE a.uid = u.id AND u.id = ?"
    areas = db.query(sql, [uid])
    sql = "SELECT i.id FROM items i, users u WHERE i.uid = u.id AND u.id = ?"
    items = db.query(sql, [uid])
    return render_template("user.html", user=user, area_count=len(areas), item_count=len(items), areas=areas)

@app.route("/new_area")
def new_area():
    sql = "SELECT value FROM tags"
    all_tags = db.query(sql)
    return render_template("new_area.html", all_tags=all_tags)

@app.route("/create_area", methods=["POST"])
def create_area():
    helper.require_login()
    helper.check_csrf()
    name = request.form.get("name")
    description = request.form.get("description")
    image = request.files["image"]
    set_tags = request.form.getlist("tag")
    if not name or not description or not image:
        return "Form is missing fields.", 400
    
    if image.mimetype != "image/jpeg":
        return "File is not a JPEG image.", 400
    file = image.read()
    if len(file) > 1024 * 1024:
        return "File is over 1 MB.", 400

    sql = "INSERT INTO areas (uid, name, description, image) VALUES (?, ?, ?, ?)"
    db.execute(sql, [session["uid"], name, description, file])

    aid = db.last_insert_id()

    sql = "INSERT INTO area_tags (aid, value) VALUES (?, ?)"
    for tag in set_tags:
        db.execute(sql, [aid, tag])
    
    return redirect("/area/"+str(aid))

@app.route("/create_item", methods=["POST"])
def create_item():
    helper.require_login()
    helper.check_csrf()
    name = request.form.get("name")
    aid = request.form.get("aid")
    image = request.files["image"]
    if not name or not aid or not image:
        return "Form is missing fields.", 400
    query = areas.get_area(aid)
    if not query:
        abort(404)
    if image.mimetype != "image/jpeg":
        return "File is not a JPEG image.", 400
    file = image.read()
    if len(file) > 1024 * 1024:
        return "File is over 1 MB.", 400

    sql = "INSERT INTO items (uid, aid, name, image) VALUES (?, ?, ?, ?)"
    db.execute(sql, [session["uid"], aid, name, file])

    return redirect("/area/"+str(aid))

@app.route("/areas")
def list_areas():
    keyword = request.args.get("keyword") or ""
    restrict = request.args.get("restrict") or ""
    tag = request.args.get("tag") or ""
    print(tag)
    query = None
    if keyword:
        word = "%"+keyword+"%"
        if restrict == "name":
            sql = "SELECT DISTINCT a.id id, a.uid uid, a.name name, u.username author FROM users u, areas a LEFT JOIN area_tags at ON at.aid = a.id WHERE a.uid = u.id AND (a.name LIKE ?) AND at.aid = a.id AND (at.value = ? OR ? = '')"
            query = db.query(sql, [word, tag, tag])
        elif restrict == "description":
            sql = "SELECT DISTINCT a.id id, a.uid uid, a.name name, u.username author FROM users u, areas a LEFT JOIN area_tags at ON at.aid = a.id WHERE a.uid = u.id AND (a.description LIKE ?) AND at.aid = a.id AND (at.value = ? OR ? = '')"
            query = db.query(sql, [word, tag, tag])
        elif restrict == "author":
            sql = "SELECT DISTINCT a.id id, a.uid uid, a.name name, u.username author FROM users u, areas a LEFT JOIN area_tags at ON at.aid = a.id WHERE a.uid = u.id AND (u.username LIKE ?) AND at.aid = a.id AND (at.value = ? OR ? = '')"
            query = db.query(sql, [word, tag, tag])
        else:
            sql = "SELECT DISTINCT a.id id, a.uid uid, a.name name, u.username author FROM users u, areas a LEFT JOIN area_tags at ON at.aid = a.id WHERE a.uid = u.id AND (a.name LIKE ? OR a.description LIKE ?) AND at.aid = a.id AND (at.value = ? OR ? = '')"
            query = db.query(sql, [word, word, tag, tag])
    else:
        sql = "SELECT DISTINCT a.id id, a.uid uid, a.name name, u.username author FROM users u, areas a LEFT JOIN area_tags at ON at.aid = a.id WHERE a.uid = u.id AND (at.value = ? OR ? = '')"
        query = db.query(sql, [tag, tag])
    sql = "SELECT value FROM tags"
    all_tags = db.query(sql)
    return render_template("areas.html", areas=query, keyword=keyword, restrict=restrict, all_tags=all_tags, filter_tag=tag)

@app.route("/area/<int:aid>")
def area(aid):
    query = areas.get_area(aid)
    if not query:
        abort(404)
    sql = "SELECT i.id, i.uid uid, i.name name, u.username author FROM users u, items i WHERE u.id = i.uid AND i.aid = ?"
    query2 = db.query(sql, [aid])
    return render_template("area.html", id=aid, area=query, items=query2)

@app.route("/area/<int:aid>/edit", methods=["GET", "POST"])
def area_edit(aid):
    if request.method == "GET":
        query = areas.get_area(aid)
        if not query:
            abort(404)
        sql = "SELECT value FROM area_tags at, areas a WHERE at.aid = a.id AND a.id = ?"
        tags = db.query(sql, [aid])
        set_tags = []
        for tag in tags:
            set_tags.append(tag["value"])
        sql = "SELECT value FROM tags"
        all_tags = db.query(sql)
        return render_template("edit_area.html", id=aid, area=query, tags=set_tags, all_tags=all_tags)
    elif request.method == "POST":
        sql = "SELECT uid FROM areas WHERE id = ?"
        query = db.query(sql, [aid])
        if not query:
            abort(404)
        helper.author_check(query[0])
        helper.check_csrf()

        name = request.form.get("name")
        description = request.form.get("description")
        image = request.files["image"]
        set_tags = request.form.getlist("tag")
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

        sql = "DELETE FROM area_tags WHERE aid = ?"
        db.execute(sql, [aid])

        sql = "INSERT INTO area_tags (aid, value) VALUES (?, ?)"
        for tag in set_tags:
            db.execute(sql, [aid, tag])
        return redirect("/area/"+str(aid))

@app.route("/item/<int:iid>/edit", methods=["GET", "POST"])
def item_edit(iid):
    if request.method == "GET":
        query = items.get_item(iid)
        if not query:
            abort(404)
        query2 = areas.get_area(query["aid"])
        if not query2:
            abort(404)
        return render_template("edit_item.html", id=iid, item=query, area=query2)
    elif request.method == "POST":
        sql = "SELECT aid, uid, id FROM items WHERE id = ?"
        query = db.query(sql, [iid])
        if not query:
            abort(404)
        aid = query[0]["aid"]
        query2 = areas.get_area(aid)
        if not query2:
            abort(404)
        print(query2[0])
        helper.author_check(query[0])
        helper.check_csrf()

        name = request.form.get("name")
        image = request.files["image"]
        if not name:
            return "Form is missing fields.", 400

        if image:
            if image.mimetype != "image/jpeg":
                return "File is not a JPEG image."
            file = image.read()
            if len(file) > 1024 * 1024:
                return "File is over 1 MB.", 400

            sql = "UPDATE items SET (name, image) = (?, ?) WHERE id = ?"
            db.execute(sql, [name, file, aid])
        else:
            sql = "UPDATE items SET (name) = (?) WHERE id = ?"
            db.execute(sql, [name, aid])
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
            helper.check_csrf()
            sql = "DELETE FROM area_tags WHERE aid = ?"
            db.execute(sql, [aid])
            sql = "DELETE FROM items WHERE aid = ?"
            db.execute(sql, [aid])
            sql = "DELETE FROM areas WHERE id = ?"
            db.execute(sql, [aid])
            return redirect("/")
        else:
            return redirect("/area/"+str(aid))

@app.route("/item/<int:iid>/delete", methods=["GET", "POST"])
def item_delete(iid):
    if request.method == "GET":
        sql = "SELECT uid, name FROM items WHERE id = ?"
        query = db.query(sql, [iid])
        if not query:
            abort(404)
        return render_template("delete_item.html", id=iid, item=query[0])
    elif request.method == "POST":
        sql = "SELECT uid, aid FROM items WHERE id = ?"
        query = db.query(sql, [iid])
        if not query:
            abort(404)
        if "confirm" in request.form:
            helper.author_check(query[0])
            helper.check_csrf()
            sql = "DELETE FROM items WHERE id = ?"
            db.execute(sql, [iid])
            return redirect("/")
        else:
            return redirect("/area/"+str(query[0]["aid"]))

@app.route("/area/<int:aid>/image")
def area_image(aid):
    sql = "SELECT image FROM areas WHERE id = ?"
    query = db.query(sql, [aid])
    if not query:
        abort(404)

    response = make_response(bytes(query[0][0]))
    response.headers.set("Content-Type", "image/jpeg")
    return response

@app.route("/item/<int:iid>/image")
def item_image(iid):
    sql = "SELECT image FROM items WHERE id = ?"
    query = db.query(sql, [iid])
    if not query:
        abort(404)

    response = make_response(bytes(query[0][0]))
    response.headers.set("Content-Type", "image/jpeg")
    return response
