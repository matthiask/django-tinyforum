from django.contrib.auth.models import User
from django.test import Client, TestCase

from tinyforum.models import Thread


class ForumTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = User.objects.create_superuser(
            "admin", "admin@example.com", "password"
        )
        cls.user1 = User.objects.create_user("user1", "user1@example.com", "password")
        cls.user2 = User.objects.create_user("user2", "user2@example.com", "password")

    def test_thread_list(self):
        c = Client()
        c.force_login(self.user1)
        response = c.get("/")
        # print(response.content.decode("utf-8"))

        response = c.post(
            "/create/", {"title": "Thread title", "text": "<p>Frsit psot.</p>"}
        )
        thread = Thread.objects.get()
        self.assertRedirects(response, thread.get_absolute_url())

        response = c.get(thread.get_absolute_url())
        print(response.content.decode("utf-8"))
        self.assertContains(response, "Frsit psot.")
