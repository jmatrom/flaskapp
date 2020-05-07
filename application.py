import os, requests

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

KEY = "tqUlAqFv2n5p3ibbp6vyUw" #API key
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


#SELECT * FROM "users" LIMIT 50
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/more", methods=["POST"])
def more():
    username = request.form.get("username")
    password = request.form.get("password")
    #result = db.execute("SELECT * FROM users").fetchall()
    result = db.execute("SELECT * FROM users WHERE username = :username and password=:password",
    {"username": username, "password": password}).fetchall()
    if len(result) == 0:
        return render_template("error.html",message="No user found.")
    else:
        session['logged_in'] = True
        return redirect(url_for('listbooks'))

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))



@app.route("/signin")
def signinpage():
    return render_template("signin.html")

@app.route("/sigin", methods=["POST"])
def signin():
    username = request.form.get("username")
    password = request.form.get("password")
    name = request.form.get("name")
    surname = request.form.get("surname")
    #TODO: mirar que no hi hagi el mateix username a la taula
    #SELECT username FROM users WHERE username = :username
    db.execute(" INSERT INTO users (name, surname, username, password)  VALUES (:name, :surname, :username, :password)",
    {"username": username, "password": password, "name": name, "surname": surname})
    db.commit()
    return render_template("signin.html") #TODO: pasar parametres per ensenyar popup/message que digui q has fet signin

@app.route("/books", methods=["POST", "GET"])
def listbooks():
    if request.method == "GET":
        books = db.execute("SELECT * from books").fetchall()
    else:
        filter = request.form.get("filter")
        books = db.execute("SELECT * from books WHERE isbn ILIKE :filter OR title ILIKE :filter OR author ILIKE :filter OR year ILIKE :filter", {"filter": "%" + filter + "%"}).fetchall()
    return render_template("books.html", books=books)

@app.route("/books/<int:book_id>")
def infobook(book_id):
        book = db.execute("SELECT * from books WHERE id = :book_id",
        {"book_id": book_id}).fetchone()
        if book is None:
            return render_template("error.html", message="No such book.")

        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": book.isbn})
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        bookapi = res.json()
        data = bookapi["books"][0]
        return render_template("book.html", book=book, bookapi=data)

        #https://www.goodreads.com/book/review_counts.json?key=tqUlAqFv2n5p3ibbp6vyUw&isbns=9781632168146
#{"books":[{"id":29207858,"isbn":"1632168146","isbn13":"9781632168146","ratings_count":1,"reviews_count":6,
#"text_reviews_count":0,"work_ratings_count":28,"work_reviews_count":129,"work_text_reviews_count":9,"average_rating":"4.14"}]}
