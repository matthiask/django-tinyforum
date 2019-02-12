from functools import wraps

from django.conf.urls import url
from django.contrib.auth.decorators import login_required

# from community.decorators import (
#     profile_required,
#     profile_required_if_authenticated,
#     moderator_required,
# )
from tinyforum import views


profile_required = login_required
profile_required_if_authenticated = login_required
moderator_required = login_required


def moderation(fn):
    @wraps(fn)
    def dec(request, *args, **kwargs):
        # kwargs["moderation"] = request.user.profile.has_moderation_powers
        kwargs["moderation"] = request.user.is_staff
        return fn(request, *args, **kwargs)

    return dec


app_name = "tinyforum"
urlpatterns = [
    url(
        r"^$", profile_required_if_authenticated(views.thread_list), name="thread-list"
    ),
    url(
        r"^create/$",
        profile_required(moderation(views.thread_form)),
        name="thread-create",
    ),
    url(
        r"^(?P<pk>[0-9]+)/$",
        profile_required_if_authenticated(views.post_list),
        name="thread-detail",
    ),
    url(
        r"^(?P<pk>[0-9]+)/update/$",
        profile_required(moderation(views.thread_form)),
        name="thread-update",
    ),
    url(
        r"^(?P<pk>[0-9]+)/star/$",
        profile_required(views.thread_star),
        name="thread-star",
    ),
    url(
        r"^post/(?P<pk>[0-9]+)/update/$",
        profile_required(moderation(views.post_form)),
        name="post-update",
    ),
    url(
        r"^post/(?P<pk>[0-9]+)/report/$",
        profile_required(views.post_report),
        name="post-report",
    ),
    url(r"^moderation/$", moderator_required(views.report_list), name="report-list"),
    url(
        r"^moderation/(?P<pk>[0-9]+)/$",
        moderator_required(views.report_handle),
        name="report-handle",
    ),
]
