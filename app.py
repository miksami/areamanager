from flask import Flask
from flask import redirect, render_template, request, session
import random
import sqlite3
import db
import config
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

@app.route("/new_area")
def new_area():
    return render_template("new_area.html")

@app.route("/create_area", methods=["POST"])
def create_area():
    pass

@app.route("/area/<int:page_id>")
def page(page_id):
    return "Area " + str(page_id)
