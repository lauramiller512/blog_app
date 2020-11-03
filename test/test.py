import json
import unittest
import mock
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

    def tearDown(self):
        # The tearDown method is called AFTER every test
        # We use it to clean up
        # In this case we delete any data that might have been
        # inserted as part of a test
        session = session_factory()
        session.query(Article).delete()
        session.query(User).delete()
        session.commit()
        session.close()

    def test_hellow_world(self):
        response = self.client.get("/json")
        self.assertEqual(
            response.get_json(), {
                "message": "hello world"
            }
        )

    def test_url_not_found(self):
        response = self.client.get("/non-existent")
        self.assertEqual(response.status_code, 404)

    def test_create_article_json(self):
        response = self.client.post("/json/articles", data=json.dumps({
            "text": "This is my article",
            "title": "Bikes are awesome",
            "created_by": "yavor.atanasov@bbc.co.uk"
        }), content_type='application/json')
        self.assertEqual(response.status_code, 201)
