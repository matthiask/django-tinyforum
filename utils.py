# Copied from feincms3/shortcuts.py

from django.core import paginator
from django.shortcuts import render


__all__ = ('template_name', 'render_list', 'render_detail')


def template_name(model, template_name_suffix):
    return '%s/%s%s.html' % (
        model._meta.app_label,
        model._meta.model_name,
        template_name_suffix,
    )


def paginate_list(request, iterable, paginate_by=None, orphans=0):
    if not paginate_by:
        return iterable

    p = paginator.Paginator(iterable, paginate_by)
    page = request.GET.get('page')
    if page == 'last':
        return p.page(p.num_pages)

    try:
        return p.page(request.GET.get('page'))
    except paginator.PageNotAnInteger:
        return p.page(1)
    except paginator.EmptyPage:
        return p.page(p.num_pages)


def render_list(request, queryset, context=None, *,
                template_name_suffix='_list',
                paginate_by=None, orphans=0):
    context = context or {}
    if paginate_by:
        p = paginator.Paginator(queryset, paginate_by)
        try:
            object_list = p.page(request.GET.get('page'))
        except paginator.PageNotAnInteger:
            object_list = p.page(1)
        except paginator.EmptyPage:
            object_list = p.page(p.num_pages)
    else:
        object_list = queryset

    context.update({
        'object_list': object_list,
        '%s_list' % queryset.model._meta.model_name: object_list,
    })
    return render(
        request,
        template_name(queryset.model, template_name_suffix),
        context,
    )


def render_detail(request, object, context=None, *,
                  template_name_suffix='_detail'):
    context = context or {}
    context.update({
        'object': object,
        object._meta.model_name: object,
    })
    return render(
        request,
        template_name(object, template_name_suffix),
        context,
    )
