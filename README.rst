================
django-tinyforum
================

.. image:: https://travis-ci.org/matthiask/django-tinyforum.svg?branch=master
   :target: https://travis-ci.org/matthiask/django-tinyforum


Add your own URLconf module:

.. code-block:: python

    from functools import wraps

    from django.conf.urls import url

    from community.decorators import (
        profile_required,
        profile_required_if_authenticated,
        moderator_required,
    )
    from tinyforum import views


    def moderation(fn):
        @wraps(fn)
        def dec(request, *args, **kwargs):
            kwargs["moderation"] = request.user.profile.has_moderation_powers
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
