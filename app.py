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

app = Flask(__name__)

EMAIL_PATTERN = r"^([a-z]+)\.([a-z]+)\d*@bbc\.co\.uk$"

users = {
    1: User("Yav", "Yavor", "Atanasov"),
    2: User("Loz", "Laura", "Miller")
}

articles = {
    1: Article("Sample text", "First Article", users[1]),
    2: Article("Another sample text", "Second Article", users[2])
}

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
    if request.method == "GET":
        response = []
        for article in articles.values():
            response.append({
                "title": article.title
            })
        return Response(json.dumps(response), mimetype="application/json")
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
    return render_template("articles.html", articles=articles)

@app.route("/articles/<int:article_id>")
@measure_time
def get_article_id_html(article_id):
    try:
        return render_template("article_id.html", article=articles[article_id])
    except KeyError:
        raise NotFound

@app.route("/articles/create", methods=["GET", "POST"])
@measure_time
def create_article():
    t0 = time()
    if request.method == "GET":
        t1 = time()
        logging.warn("Time taken: {0}".format(t0-t1))
        return render_template("create_article.html")
    else:
        result = request.form
        logging.warn(result)

        email = result["email"]
        m = re.match(EMAIL_PATTERN, email)
        if m is None:
            raise BadRequest("Invalid email address")
        fname, lname = m.groups()        

        user = User("_".join([fname, lname]), fname, lname)

        articles[max(articles.keys()) + 1] = Article(result["text"], result["title"], user)
        logging.info("Article created")
        logging.debug("Article created")

        t1 = time()
        return render_template("/articles.html", articles=articles)
    
        

#list of articles should be linked to specific article, displaying title plus text
#endpoint for article_id to also have html 404 error message
    

