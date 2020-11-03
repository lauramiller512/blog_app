
from flask import Flask, Response, render_template
from flask import request
from werkzeug.exceptions import NotFound, BadRequest
import json
import re
import logging
from functools import wraps
from time import time

from models.user import User
from models.article import Article
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, mapper, relationship
import sqlalchemy

app = Flask(__name__)

EMAIL_PATTERN = r"^([a-z]+)\.([a-z]+)\d*@bbc\.co\.uk$"

engine = create_engine(
    'postgresql://blog-app-user:lantern_rouge@127.0.0.1:5432/blog-app-db',
    pool_size=20
)

session_factory = sessionmaker(bind=engine)


def map_tables(engine):
    meta = sqlalchemy.MetaData()
    meta.reflect(bind=engine)
    t = meta.tables
    mapper(User, t["authors"])
    mapper(Article, t["articles"], properties={
        "created_by": relationship(User)
        })


map_tables(engine)


def measure_time(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        t0 = time()
        result = f(*args, **kwargs)
        t1 = time()
        logging.warn("Time taken: {0}".format(t1-t0))
        return result
    return decorated_function


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
    session = session_factory()
    if request.method == "GET":
        articles = session.query(Article).all()
        return Response(json.dumps(
            [{"title": i.title} for i in articles]
        ), mimetype="application/json") # necessary as browser otherwise will treat results as html
    else:
        data = request.json
        try:
            article = Article(data["text"],
                data["title"],
                data["created_by"])
            session.add(article)
            session.commit()
        except KeyError:
            raise BadRequest("Invalid data provided")
        return (
            Response(json.dumps(
                {"message": "Okay"}), mimetype="application/json"),
            201
            )


@app.route("/json/articles/<uuid:article_id>", methods=["GET", "DELETE"])
@measure_time
def get_article(article_id):
    session = session_factory()
    article = session.query(Article).filter_by(id=str(article_id)).first()
    if article is None:
        raise NotFound("This article cannot be found")
    if request.method == "GET":
        new_dict = {
            "title": article.title,
            "text": article.txt,
            "created_by": article.created_by.username
        }
        return Response(json.dumps(new_dict), mimetype="application/json")
    else:
        session.delete(article)
        session.commit()
        return "", 204


@app.route("/articles")
@measure_time
def get_articles_html():
    session = session_factory()
    articles = session.query(Article).all()
    return render_template("articles.html", articles=articles)


@app.route("/articles/<uuid:article_id>")
@measure_time
def get_article_id_html(article_id):
    session = session_factory()
    article = session.query(Article).filter_by(id=str(article_id)).first()
    logging.warn(article)
    try:
        return render_template("article_id.html", article=article)
    except KeyError:
        raise NotFound


@app.route("/articles/create", methods=["GET", "POST"])
@measure_time
def create_article():
    session = session_factory()

    if request.method == "GET":
        return render_template("create_article.html")
    title = request.form["title"]
    text = request.form["text"]
    logging.warn(text)
    email = request.form["email"]
    logging.warn(1)

    m = re.match(EMAIL_PATTERN, email)
    if m is None:
        raise BadRequest("Invalid email address")
    fname, lname = m.groups()
    username = "_".join([fname, lname])
    user = User(username, fname, lname)
    # two insert statements, db will throw error if username not unique
    session.add(user)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError:
        session.rollback()
        user = session.query(User).filter_by(username=username).first()

    article = Article(text, title, user)
    session.add(article)
    session.commit()
    logging.warn(article.text)

    articles = session.query(Article).all()

    return render_template("/articles.html", articles=articles)


if __name__ ==  "__main__":
    main()
