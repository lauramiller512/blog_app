import json
import unittest
from mock import patch
import requests
from app import app, session_factory
from models.article import Article
from models.user import User

class TestGetRequest(unittest.TestCase):

    def setUp(self):
        # The setUp method is called BEFORE every test
        # We use it to do some common setup for each test
        app.testing = True
        self.client = app.test_client()
        self.session = session_factory()


    def tearDown(self):
        # The tearDown method is called AFTER every test
        # We use it to clean up
        # In this case we delete any data that might have been
        # inserted as part of a test
        self.session.query(Article).delete()
        self.session.query(User).delete()
        self.session.commit()
        self.session.close()

    def test_hello_world(self):
        response = self.client.get("/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(), {
                "message": "hello world"
            }
        )

    def test_url_not_found(self):
        response = self.client.get("/non-existent")
        self.assertEqual(response.status_code, 404)

    def test_get_articles_json_empty(self):
        response = self.client.get("/json/articles")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(), []
        )

    def test_get_articles_json(self):
        user = User("laura_miller", "laura", "miller")
        article =  Article("Some text", "A Title", user)
        article_two = Article("Other text", "Other article", user)
        self.session.add_all([user, article, article_two])
        self.session.commit()
        response = self.client.get("/json/articles")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(), [
                {
                    "title": "A Title"
                },
                {
                    "title": "Other article"
                }
            ]
        )

    def test_get_article_json(self):
        user = User("laura_miller", "laura", "miller")
        article =  Article("Some text", "A Title", user)
        self.session.add_all([user, article])
        self.session.commit()
        response = self.client.get("/json/articles/{0}".format(article.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(), {
                "title": article.title,
                "text": article.text,
                "created_by": article.created_by.username
            }
        )

    def test_get_article_json_invalid(self):
        response = self.client.get("/json/articles/{0}".format("e6412fa2-ac6b-4a97-984a-2add7a0920fb"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get_json(), {
                "error": "404 Not Found: This article cannot be found"
            }
        )


    def test_create_article_json(self):
        response = self.client.post("/json/articles", data=json.dumps({
            "text": "This is my article",
            "title": "Bikes are awesome",
            "created_by": "yavor.atanasov@bbc.co.uk"
        }), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json(), {
                "message": "Okay"
            }
        )

        article = self.session.query(Article).first()
        self.assertEqual(
            article.title, "Bikes are awesome"
        )

    def test_delete_article_json(self):
        user = User("laura_miller", "laura", "miller")
        article =  Article("Some text", "A Title", user)
        self.session.add_all([user, article])
        self.session.commit()

        response = self.client.delete("/json/articles/{0}".format(article.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            response.get_json(), None)


    @patch("app.logging")
    def test_create_article_json_invalid_email(self, mocked_logging):
        response = self.client.post("/json/articles", data=json.dumps({
            "text": "This is my article",
            "title": "Bikes are awesome",
            "created_by": "yavor.atanasov@gmail"
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(), {
                "error": "400 Bad Request: Invalid email address"
            }
        )
        mocked_logging.warning.assert_called_once_with("400 Bad Request: Invalid email address")

    @patch("app.logging")
    def test_create_article_json_invalid_input(self, mocked_logging):
        response = self.client.post("/json/articles", data=json.dumps({
            "text": "This is my article",
            "created_by": "yavor.atanasov@bbc.co.uk"
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(), {
                "error": "400 Bad Request: Invalid data provided"
            }
        )
        mocked_logging.warning.assert_called_once_with("400 Bad Request: Invalid data provided")

    def test_create_article_html_form(self):
        response = self.client.post("/articles/create", data=dict(
            text="This is my article",
            title="Bikes are awesome",
            created_by="yavor.atanasov@bbc.co.uk"
        ), content_type='application/x-www-form-urlencoded')
        print(response.get_data())
        self.assertEqual(response.status_code, 200)

        article = self.session.query(Article).first()
        self.assertEqual(
            article.title, "Bikes are awesome"
        )


# test for get json/articles if given non-existant uuid. raise proper error
# test for delete /json/articles/<uuid:article_id>; check status code and response body is empty
