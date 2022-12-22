import os
import re
from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

#Configure application
app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@app.route("/index")
@login_required
def index(course=None):
    """Show page"""
    courses = db.execute("SELECT course FROM courses")
    for row in courses:
        if course == row["course"]:
            grades = db.execute("SELECT * FROM grades WHERE course = ? AND user_id = ?", course, session["user_id"])
            return render_template("index.html", grades=grades, courses=courses)
    grades = db.execute("SELECT * FROM grades WHERE user_id = ?", session["user_id"])
    return render_template("index.html", grades=grades, courses=courses)


@app.route("/filter", methods=["POST"])
@login_required
def filter():
    course = request.form.get("course-filter")
    return index(course)

@app.route("/view", methods=["GET", "POST"])
@login_required
def view():
    grades_sum = 0
    grades_nr = 0
    averages = {}
    courses = db.execute("SELECT course FROM courses")
    
    for row in courses:
        grades_sum = 0
        grades_nr = 0
        grades = db.execute("SELECT grade FROM grades WHERE course = ? AND user_id = ?", row["course"], session["user_id"])
        for grade in grades:
            grades_sum += grade["grade"]
            grades_nr += 1
        if grades_nr > 0:
            averages[row["course"]] = round(grades_sum / grades_nr, 3)

    avs = 0
    av_nr = 0
    for average in averages.keys():
        avs += averages[average]
        av_nr += 1

    total_averages = round(avs / av_nr, 2)
    


    return render_template("view.html", averages=averages, total_averages=total_averages)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via GET
    if request.method == "POST":
        
        error = None
        username = request.form.get("username")
        password = request.form.get("password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1:
            error = "The username you entered isn't connected to an account."
            return render_template("login.html", error=error)
        if not check_password_hash(rows[0]["hash"], password):
            error = "The password you've entered is incorrect."
            return render_template("login.html", error=error)
        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        

        flash("You were successfully logged in!")
            
        
        return redirect("/")
    else:
        return render_template("login.html")
        


@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via GET
    if request.method == "GET":
        return render_template("register.html")
    else:
        error = None
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        rows = db.execute("SELECT id FROM users WHERE username = ?", username)

        if len(rows) != 0:
            error = "This username is already taken."
            return render_template("register.html", error=error)
        if not email:
            error = "Please provide a valid email."
            return render_template("register.html", error=error)

        rows = db.execute("SELECT id FROM users WHERE email = ?", email)
        if len(rows) != 0:
            error = "This email is already used"
            return render_template("register.html", error=error)

        if not username:
            error = "Please provide a valid username."
            return render_template("register.html", error=error)
        if not password:
            error = "Please provide a valid password."
            return render_template("register.html", error=error)
        if not confirm:
            error = "Please provide a password confirmation."
            return render_template("register.html", error=error)
        if password != confirm:
            error = "Passwords do not match."
            return render_template("register.html", error=error)
        if not re.search("^[a-zA-Z0-9_]+@\w+\.[a-zA-Z]+$", email):
            error = "Invalid email."
            return render_template("register.html", error=error)
        if len(password) < 6:
            error = "Password should contain atleast 6 characters."
            return render_template("register.html", error=error)

        # Insert user into database

        db.execute("INSERT INTO users (email, username, hash) VALUES (?, ?, ?)", email, username, generate_password_hash(password))
        flash("You were successfully registered!")
        return redirect("/login")

        
@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "GET":
        courses = db.execute("SELECT course FROM courses")
        return render_template("add.html", courses=courses)
    else:
        error = None
        course = request.form.get("course")
        grade = int(request.form.get("grade"))
        courses = db.execute("SELECT course FROM courses")
        rows = db.execute("SELECT * FROM courses WHERE course = ?", course)
        if len(rows) != 1:
            error = "Invalid course"
            return render_template("add.html", error=error, courses=courses)
        if grade > 10 or grade < 1:
            error = "Invalid grade"
            return render_template("add.html", error=error, courses=courses)
        user_id = session["user_id"]
        db.execute("INSERT INTO grades (user_id, grade, course, date) VALUES (?, ?, ?, ?)", user_id, grade, course, datetime.now())

        return redirect("/")
        

