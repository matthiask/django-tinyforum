# from django import forms
from django.forms.models import modelform_factory
# from django.utils.translation import

from tinyforum.models import Thread, Post


def form_for_thread(request, instance, moderation=False):
    fields = ['title']
    if moderation:
        fields.extend(['is_pinned', 'closed_at', 'moderation_status'])
    elif instance and request.user == instance.authored_by:
        fields.extend(['closed_at'])
    return modelform_factory(Thread, fields=fields)


def form_for_post(request, instance, moderation=False):
    fields = ['text']
    if moderation:
        fields.extend(['moderation_status'])
    return modelform_factory(Post, fields=fields)
