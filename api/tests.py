from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from time import sleep

from .models import Article, Rating
from .serializers import RateArticleSerializer, UserSerializer


class LoginAndRateArticleTest(TestCase):

    def setUp(self):
        # Create a test user
        self.test_user1 = User.objects.create_user(username="test_user1", password="test_password1",
                                                   email="test1@test.com")
        self.test_user2 = User.objects.create_user(username="test_user2", password="test_password2",
                                                   email="test2@test.com")
        self.test_user3 = User.objects.create_user(username="test_user3", password="test_password3",
                                                   email="test3@test.com")
        self.test_user4 = User.objects.create_user(username="test_user4", password="test_password4",
                                                   email="test4@test.com")

        # Create an APIClient instance for making requests
        self.client = APIClient()

    def test_login_and_create_article(self):
        # Login with the test user
        login_data = {"username": self.test_user1.username, "password": "test_password1"}
        response = self.client.post("/login/", login_data, format="json")
        self.assertEqual(response.status_code, 200)
        token1 = response.json()["token"]
        print(token1)

        test_article_data = {"title": "Test Article1", "content": "This is a test article"}
        response = self.client.post("/article/create/", test_article_data, format="json", headers={
            "Authorization": f"Token {token1}"
        })
        self.assertEqual(response.status_code, 200)
        print(response.json())
        article_id1 = response.json()["article_id"]

    def test_rate_article(self):
        login_data = {"username": self.test_user1.username, "password": "test_password1"}
        response = self.client.post("/login/", login_data, format="json")
        self.assertEqual(response.status_code, 200)
        token1 = response.json()["token"]
        print(token1)

        test_article_data = {"title": "Test Article1", "content": "This is a test article"}
        response = self.client.post("/article/create/", test_article_data, format="json", headers={
            "Authorization": f"Token {token1}"
        })
        self.assertEqual(response.status_code, 200)
        print(response.json())
        article_id1 = response.json()["article_id"]

        login_data = {"username": self.test_user2.username, "password": "test_password2"}
        response = self.client.post("/login/", login_data, format="json")
        self.assertEqual(response.status_code, 200)
        token2 = response.json()["token"]
        print(token2)

        test_article_data = {"title": "Test Article2", "content": "This is a test article"}
        response = self.client.post("/article/create/", test_article_data, format="json", headers={
            "Authorization": f"Token {token2}"
        })
        self.assertEqual(response.status_code, 200)
        print(response.json())
        article_id2 = response.json()["article_id"]

        rate_data = {"article_id": article_id1, "rate": 5}
        response = self.client.post("/article/rate/", rate_data,
                                    headers={
                                        "Authorization": f"Token {token2}"
                                    })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "rate is saved")
        sleep(5)

        response = self.client.get("/articles/", rate_data,
                                    headers={
                                        "Authorization": f"Token {token2}"
                                    })
        self.assertEqual(response.json()[0]['user_rating'], 5)

