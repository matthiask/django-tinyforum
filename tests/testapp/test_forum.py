from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse

from tinyforum.forms import form_for_post, form_for_thread
from tinyforum.models import Post, PostReport, Thread


def messages(response):
    return [m.message for m in get_messages(response.wsgi_request)]


class ForumTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = User.objects.create_superuser(
            "admin", "admin@example.com", "password"
        )
        cls.user1 = User.objects.create_user("user1", "user1@example.com", "password")
        cls.user2 = User.objects.create_user("user2", "user2@example.com", "password")

    def test_posting_a_bit(self):
        c = Client()
        c.force_login(self.user1)

        response = c.get("/create/")
        self.assertContains(response, 'id="id_title"')
        self.assertContains(response, 'id="id_text"')
        self.assertNotContains(response, 'id="id_is_pinned"')

        response = c.post(
            "/create/", {"title": "Thread title", "text": "<p>Frsit psot.</p>"}
        )
        thread = Thread.objects.get()
        self.assertEqual(thread.posts.count(), 1)

        self.assertRedirects(response, thread.get_absolute_url())
        self.assertEqual(thread.authored_by, self.user1)

        response = c.get(thread.get_absolute_url())
        self.assertContains(response, "Frsit psot.")

        response = c.get(thread.get_absolute_url() + "update/")
        self.assertEqual(response.status_code, 200)

        c = Client()
        c.force_login(self.user2)
        response = c.post(thread.get_absolute_url(), {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(thread.posts.count(), 1)

        response = c.post(thread.get_absolute_url(), {"text": "<p>Second!</p>"})
        self.assertRedirects(response, "%s?page=last" % thread.get_absolute_url())
        self.assertEqual(thread.posts.count(), 2)

        response = c.get(thread.get_absolute_url() + "update/")
        self.assertRedirects(response, thread.get_absolute_url())
        self.assertEqual(messages(response), ["Sorry, you do not have permissions."])

        c = Client()
        c.force_login(self.user1)
        response = c.get(thread.get_absolute_url() + "update/")
        self.assertContains(response, 'for="id_close_thread"')

        response = c.post(
            thread.get_absolute_url() + "update/",
            {"title": thread.title, "close_thread": True},
        )
        self.assertRedirects(response, thread.get_absolute_url())

        thread.refresh_from_db()
        self.assertFalse(thread.closed_at is None)

        response = c.get(thread.get_absolute_url() + "update/")
        self.assertNotContains(response, 'for="id_close_thread"')

        response = c.get("/?status=closed")
        self.assertContains(response, 'href="/%s/?page=last"' % thread.pk)

    def test_thread_list(self):
        Thread.objects.create(title="One", authored_by=self.user1)
        Thread.objects.create(title="Two", authored_by=self.user1)

        c = Client()
        response = c.get("/")
        self.assertContains(response, "data-set-status", 0)

        c.force_login(self.user2)
        response = c.get("/")
        self.assertContains(response, "data-set-status", 2)
        # print(response.content.decode("utf-8"))

    def test_thread_update(self):
        t = Thread.objects.create(title="One", authored_by=self.user1)

        c = Client()
        c.force_login(self.user1)
        response = c.get(t.get_absolute_url() + "update/")
        self.assertContains(response, 'id="id_title"')
        self.assertContains(response, 'id="id_close_thread"')
        self.assertNotContains(response, 'id="id_is_pinned"')
        self.assertNotContains(response, 'id="id_moderation_status"')

        response = c.post(t.get_absolute_url() + "update/", {"title": "Two"})
        self.assertRedirects(response, t.get_absolute_url())
        self.assertEqual(messages(response), [])

        t.refresh_from_db()
        self.assertEqual(t.title, "Two")

        c.force_login(self.user2)
        response = c.post(t.get_absolute_url() + "update/", {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(messages(response), ["Sorry, you do not have permissions."])

        c.force_login(self.admin)
        response = c.get(t.get_absolute_url() + "update/")
        self.assertContains(response, 'id="id_title"')
        self.assertContains(response, 'id="id_close_thread"')
        self.assertContains(response, 'id="id_is_pinned"')
        self.assertContains(response, 'id="id_moderation_status"')

    def test_post_update(self):
        t = Thread.objects.create(title="One", authored_by=self.user1)
        p = Post.objects.create(thread=t, text="One text", authored_by=self.user1)
        p_update_url = reverse("tinyforum:post-update", kwargs={"pk": p.pk})

        c = Client()
        c.force_login(self.user1)
        response = c.get(p_update_url)
        self.assertContains(response, 'id="id_text"')
        self.assertNotContains(response, 'id="id_moderation_status"')

        response = c.post(p_update_url, {"text": "Two text"})
        self.assertRedirects(response, t.get_absolute_url())
        self.assertEqual(messages(response), [])

        p.refresh_from_db()
        self.assertEqual(p.text, "Two text")

        c.force_login(self.user2)
        response = c.post(p_update_url, {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(messages(response), ["Sorry, you do not have permissions."])

        c.force_login(self.admin)
        response = c.get(p_update_url)
        self.assertContains(response, 'id="id_text"')
        self.assertContains(response, 'id="id_moderation_status"')

    def test_anonymous(self):
        c = Client()
        self.assertEqual(c.get("/").status_code, 200)
        self.assertRedirects(c.get("/create/"), "/accounts/login/?next=/create/")

        t = Thread.objects.create(title="Test", authored_by=self.user1)
        self.assertEqual(c.get(t.get_absolute_url()).status_code, 200)
        self.assertEqual(c.get(t.get_absolute_url() + "update/").status_code, 302)
        self.assertEqual(c.get(t.get_absolute_url() + "star/").status_code, 403)

    def test_user(self):
        c = Client()
        c.force_login(self.user1)
        response = c.get("/moderation/")
        self.assertRedirects(response, "/")
        self.assertEqual(messages(response), ["You do not have moderation powers."])

    def test_moderator(self):
        c = Client()
        c.force_login(self.admin)
        self.assertEqual(c.get("/moderation/").status_code, 200)

        response = c.get("/create/")
        self.assertContains(response, 'id="id_title"')
        self.assertContains(response, 'id="id_text"')
        self.assertContains(response, 'id="id_is_pinned"')

        t = Thread.objects.create(title="One", authored_by=self.user1)
        response = c.get(t.get_absolute_url())
        self.assertContains(response, 'id="id_text"')
        self.assertNotContains(response, 'id="id_moderation_status_0"')

    def test_form_functions(self):
        request = SimpleNamespace(method="GET", user=AnonymousUser())

        self.assertEqual(form_for_thread(request), None)
        self.assertEqual(form_for_post(request, thread=42), None)

    def test_post_report(self):
        t = Thread.objects.create(title="One", authored_by=self.user1)
        p = Post.objects.create(thread=t, text="One text", authored_by=self.user1)
        p_report_url = reverse("tinyforum:post-report", kwargs={"pk": p.pk})

        c = Client()
        c.force_login(self.user2)

        response = c.get(p_report_url)
        self.assertContains(response, 'id="id_reason_0"')
        self.assertContains(response, 'id="id_notes"')

        response = c.post(p_report_url, {})
        self.assertEqual(response.status_code, 200)

        response = c.post(p_report_url, {"reason": "spam", "notes": "stuff"})
        self.assertRedirects(response, t.get_absolute_url())
        self.assertEqual(
            messages(response),
            [
                "Thank you for the report. A community moderator will"
                " deal with it as soon as possible!"
            ],
        )

        response = c.get(p_report_url)
        self.assertRedirects(response, t.get_absolute_url())
        self.assertEqual(messages(response), ["You already reported this post."])

        p.refresh_from_db()
        self.assertEqual(p.moderation_status, p.FLAGGED)

        c = Client()
        c.force_login(self.admin)

        response = c.get("/moderation/")
        self.assertRegex(response.content.decode("utf-8"), "It&#(39|x27);s spam")

        r = PostReport.objects.get()
        r_handle_url = reverse("tinyforum:report-handle", kwargs={"pk": r.pk})

        response = c.get(r_handle_url)
        self.assertContains(response, 'id="id_moderation_status_0"')

        response = c.post(r_handle_url, {})
        self.assertEqual(response.status_code, 200)

        response = c.post(r_handle_url, {"moderation_status": "hidden"})
        self.assertRedirects(response, "/moderation/")

        p.refresh_from_db()
        self.assertEqual(p.moderation_status, "hidden")

        response = c.post(p_report_url, {"reason": "spam", "notes": "stuff"})
        self.assertRedirects(response, t.get_absolute_url())
        self.assertEqual(
            messages(response),
            [
                "Thank you for the report. A community moderator will"
                " deal with it as soon as possible!"
            ],
        )

        # Still hidden
        p.refresh_from_db()
        self.assertEqual(p.moderation_status, "hidden")

    def test_thread_star(self):
        t = Thread.objects.create(title="One", authored_by=self.user1)
        t_star_url = reverse("tinyforum:thread-star", kwargs={"pk": t.pk})

        self.assertEqual(t.starred_by.count(), 0)

        c = Client()
        response = c.get(t_star_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(t.starred_by.count(), 0)

        c.force_login(self.user2)
        response = c.get(t_star_url + "?status=1")
        self.assertContains(response, '"status": 1')
        self.assertEqual(t.starred_by.count(), 1)

        response = c.get(t_star_url + "?status=0")
        self.assertContains(response, '"status": 0')
        self.assertEqual(t.starred_by.count(), 0)

    def test_post_str(self):
        t = Thread.objects.create(title="One", authored_by=self.user1)
        p = Post.objects.create(
            thread=t,
            authored_by=self.user1,
            text="<p>Lorem ipsum dolor sit amet.</p> " * 20,
        )
        self.assertEqual(
            str(p),
            "Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet. Lorem"
            " ipsum dolor sit amet. Lorem ipsum dolor sit amet....",
        )

    def test_thread_absolute_url(self):
        t = Thread.objects.create(title="One", authored_by=self.user1)
        url = t.get_absolute_url()

        t.moderation_status = t.FLAGGED
        self.assertEqual(t.get_absolute_url(), url)

        t.moderation_status = t.HIDDEN
        self.assertEqual(t.get_absolute_url(), "/")
