
from flask import Flask, Response, render_template
from flask import request
from werkzeug.exceptions import NotFound, BadRequest
import json
import re
import logging
from functools import wraps
from time import time
import psycopg2

from models.user import User
from models.article import Article
from contextlib import contextmanager

app = Flask(__name__)

EMAIL_PATTERN = r"^([a-z]+)\.([a-z]+)\d*@bbc\.co\.uk$"


def get_database_connection():
    conn = psycopg2.connect("dbname='blog-app-db' user='blog-app-user' host='127.0.0.1' password='lantern_rouge'")
    return conn

def measure_time(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        t0 = time()
        result = f(*args, **kwargs)
        t1 = time()
        logging.warn("Time taken: {0}".format(t1-t0))
        return result
    return decorated_function

def db_connection():
    connection = get_database_connection()
    cur = connection.cursor()
    return cur  

def insert_article(title, text, author_id):
    with get_database_connection() as connection:
        with connection.cursor() as cur:
            cur.execute(
                """INSERT into articles(title, txt, author_id) 
                values (%s, %s, %s)""", 
                (title, text, author_id)
                )

@contextmanager
def run_query(*query_args):
    with get_database_connection() as connection:
        with connection.cursor() as cur:
            cur.execute(*query_args)
            yield cur

@app.errorhandler(BadRequest)
def bad_request(bad_request):
    logging.warn(str(bad_request))
    return Response(json.dumps({"error": str(bad_request)})), 400

@app.errorhandler(NotFound)
def not_found(error):
    if request.path.startswith("/json"):
        return Response(json.dumps({"error": str(error)})), 404
    else:
        return render_template("not_found.html"), 404

@app.route("/json")
def hello_world():
    return {
        "message": "hello world"
    }

@app.route("/json/articles", methods=["GET", "POST"])
@measure_time
def get_articles():
    if request.method == "GET":
        articles = retrieve_articles()   
        return Response(json.dumps(articles), mimetype="application/json")
    else:
        data = request.json
        try:
            articles[max(articles.keys()) + 1] = Article(data["text"], data["title"], data["created_by"])
        except KeyError:
            raise BadRequest("Invalid data provided")
        return (
            Response(json.dumps({"message": "Okay"}), mimetype="application/json"),
            201
            )


@app.route("/json/articles/<int:article_id>", methods=["GET", "DELETE"])
@measure_time
def get_article(article_id):
    if request.method == "GET":
        try:
            article = articles[article_id]
            new_dict = {
                "title": article.title,
                "text": article.text,
                "author": article.created_by.username
            }
        except KeyError:
            raise NotFound("This article cannot be found")

        return Response(json.dumps(new_dict), mimetype="application/json")
    else:
        try:
            del articles[article_id]
            return "", 204
        except KeyError:
            raise NotFound("Article you're trying to delete does not exist")


@app.route("/articles")
@measure_time
def get_articles_html():
    with run_query("""SELECT id, title from articles""") as cur:
        articles = cur.fetchall()
    return render_template("articles.html", articles=articles)

@app.route("/articles/<uuid:article_id>")
@measure_time
def get_article_id_html(article_id):
    with run_query("""SELECT title, txt, author_id from articles where id=%s""", (str(article_id), )) as cursor:
        article = cursor.fetchone()
    if article is None:
        raise NotFound
    logging.warn(article)
    with run_query("""SELECT username, firstname, lastname from authors where id=%s""", (article[2], )) as cursor:
        user = cursor.fetchone()
    user = User(*user)
    article = Article(article[1], article[0], user)
    logging.warn(article)
    try:
        return render_template("article_id.html", article=article)
    except KeyError:
        raise NotFound

@app.route("/articles/create", methods=["GET", "POST"])
@measure_time
def create_article():
    connection = get_database_connection()
    cur = connection.cursor()
    if request.method == "GET":
        return render_template("create_article.html")
    else:
        title = request.form["title"]
        text = request.form["text"]

        email = request.form["email"]
        logging.warn(1)

        m = re.match(EMAIL_PATTERN, email)
        if m is None:
            raise BadRequest("Invalid email address")
        fname, lname = m.groups()        
        username = "_".join([fname, lname])
        user = User(username, fname, lname)
        # two insert statements, db will throw error if username not unique

        logging.warn(2)

        try:
            run_query(
                """INSERT into authors(firstname, lastname, username) 
                values (%s, %s, %s)""",
                (fname, lname, username)
                )

            with run_query("""SELECT id from authors where username=%s""", (username, )) as cursor:
                author = cursor.fetchone()
        except psycopg2.errors.UniqueViolation:
            with run_query("""SELECT id from authors where username=%s""", (username, )) as cursor:
                author = cursor.fetchone()

        logging.warn(4)

        try:
            run_query(
                """INSERT into articles(title, txt, author_id) values (%s, %s, %s)""", 
                (title, text, author[0]))
            logging.warn("article written")

        except Exception as e:
            logging.warn(e)
        
        logging.warn(5)

        with run_query("""SELECT id, title from articles""") as cur:
            articles = cur.fetchall()

        return render_template("/articles.html", articles=articles)
    
        

#list of articles should be linked to specific article, displaying title plus text
#endpoint for article_id to also have html 404 error message
    

