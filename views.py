from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _

from tinyforum.forms import (
    form_for_thread, form_for_post,
    CreatePostReportForm, HandlePostReportForm,
)
from tinyforum.models import Thread, Post, PostReport
from tinyforum.utils import paginate_list, render_detail, render_list


def thread_list(request):
    return render_list(
        request,
        Thread.objects.active().select_related(
            'authored_by__profile',
            'latest_post',
        ),
        paginate_by=50,
    )


def post_list(request, pk):
    thread = get_object_or_404(Thread.objects.visible(), pk=pk)
    if request.method == 'POST':
        form = form_for_post(request, thread=thread)
        if form.is_valid():
            form.save()
            return redirect(thread.get_absolute_url() + '?page=last')
    else:
        form = None

    posts = paginate_list(
        request,
        thread.posts.visible().select_related('authored_by__profile'),
        paginate_by=20,
        orphans=5,
    )

    if form is None and posts.paginator.num_pages == posts.number:
        form = form_for_post(request, thread=thread)

    return render(request, 'tinyforum/post_list.html', {
        'object_list': posts,
        'post_list': posts,
        'thread': thread,
        'form': form,
    })


def thread_form(request, *, pk=None, moderation=False):
    instance = pk and get_object_or_404(Thread, pk=pk)
    form = form_for_thread(request, instance=instance, moderation=moderation)

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
            'moderation': (
                moderation and
                instance and
                instance.authored_by != request.user
            ),
        },
        template_name_suffix='_form',
    )


def thread_star(request, pk):
    instance = get_object_or_404(Thread, pk=pk)
    status = bool(int(request.GET.get('status')))

    if status:
        instance.starred_by.add(request.user)
    else:
        instance.starred_by.remove(request.user)

    return JsonResponse({
        'thread': instance.pk,
        'status': int(status),
    })


def post_form(request, *, pk, moderation=False):
    instance = get_object_or_404(Post.objects.select_related('thread'), pk=pk)
    form = form_for_post(
        request,
        thread=instance.thread,
        instance=instance,
        moderation=moderation,
    )

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
            'moderation': (
                moderation and
                instance.authored_by != request.user
            ),
        },
        template_name_suffix='_form',
    )


def post_report(request, *, pk):
    instance = get_object_or_404(Post, pk=pk)
    if instance.reports.filter(authored_by=request.user).exists():
        messages.info(request, _('You already reported this post.'))
        return redirect(instance.thread)

    kw = {'request': request, 'post': instance}
    if request.method == 'POST':
        form = CreatePostReportForm(request.POST, **kw)
        if form.is_valid():
            form.save()
            messages.success(request, _(
                'Thank you for the report. A community moderator will'
                ' deal with it as soon as possible!'
            ))
            return redirect(instance.thread)
    else:
        form = CreatePostReportForm(**kw)

    return render(request, 'tinyforum/report_form.html', {
        'post': instance,
        'form': form,
    })


def report_list(request):
    return render_list(
        request,
        PostReport.objects.filter(
            handled_at__isnull=True,
        ).order_by(
            'created_at',
        ).select_related(
            'post__authored_by__profile',
            'authored_by__profile',
        ),
    )


def report_handle(request, *, pk):
    instance = get_object_or_404(
        PostReport.objects.filter(handled_at__isnull=True),
        pk=pk,
    )
    kw = {'request': request, 'instance': instance}
    if request.method == 'POST':
        form = HandlePostReportForm(request.POST, **kw)
        if form.is_valid():
            form.save()
            return redirect('tinyforum:report-list')
    else:
        form = HandlePostReportForm(**kw)
    return render(request, 'tinyforum/report_form.html', {
        'post': instance,
        'form': form,
    })
