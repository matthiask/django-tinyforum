from django import template
from django.template.loader import render_to_string


register = template.Library()


@register.simple_tag(takes_context=True)
def thread_star(context, thread):
    user = context['request'].user
    if not hasattr(user, 'starred_threads_cache'):
        user.starred_threads_cache = list(
            user.starred_threads.values_list('id', flat=True)
        )
    return render_to_string('tinyforum/thread_star.html', {
        'thread': thread,
        'status': thread.id in user.starred_threads_cache,
    })
