from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _

from tinyforum.forms import form_for_thread, form_for_post
from tinyforum.models import Thread, Post
from tinyforum.utils import render_detail, render_list


def thread_list(request):
    return render_list(
        request,
        Thread.objects.active().select_related('latest_post'),
        paginate_by=50,
    )


def thread_detail(request, pk):
    thread = get_object_or_404(Thread.objects.visible(), pk=pk)
    form = form_for_post(request, thread=thread)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect(thread)

    return render_list(
        request,
        thread.posts.visible().select_related('authored_by__profile'),
        {
            'thread': thread,
            'form': form,
        },
    )


def thread_form(request, pk=None):
    instance = pk and get_object_or_404(Thread, pk=pk)
    form = form_for_thread(request, instance=instance)  # TODO moderation?

    if form is None:
        messages.error(request, _('Sorry, you do not have permissions.'))
        return redirect(instance)

    if request.method == 'POST' and form.is_valid():
        instance = form.save()
        return redirect(instance)

    return render_detail(
        request,
        instance or Thread,
        {
            'form': form,
        },
        template_name_suffix='_form',
    )


def post_form(request, pk):
    instance = get_object_or_404(Post.objects.select_related('thread'), pk=pk)
    # TODO moderation
    form = form_for_post(request, thread=instance.thread, instance=instance)

    if form is None:
        messages.error(request, _('Sorry, you do not have permissions.'))
        return redirect(instance.thread)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect(instance.thread)

    return render_detail(
        request,
        instance,
        {
            'form': form,
        },
        template_name_suffix='_form',
    )
