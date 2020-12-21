from django.conf.urls import include, url
from django.contrib import admin


# from django.shortcuts import render


urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^accounts/", include("django.contrib.auth.urls")),
    url(r"", include("testapp.forum_urls")),
]
