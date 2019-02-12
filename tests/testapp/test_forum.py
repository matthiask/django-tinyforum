from django.contrib.auth.models import User
from django.test import Client, TestCase


class ForumTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = User.objects.create_superuser(
            "admin", "admin@example.com", "password"
        )
        cls.user1 = User.objects.create_user("user1", "user1@example.com", "password")
        cls.user2 = User.objects.create_user("user2", "user2@example.com", "password")

    def test_thread(self):
        c = Client()
        c.force_login(self.user1)
        response = c.get("/")
        print(response.content.decode("utf-8"))
