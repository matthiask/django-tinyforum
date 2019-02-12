# Copied from feincms3/shortcuts.py

from django.core.paginator import Paginator
from django.shortcuts import render


__all__ = ("template_name", "render_list", "render_detail")


def template_name(model, template_name_suffix):
    return "%s/%s%s.html" % (
        model._meta.app_label,
        model._meta.model_name,
        template_name_suffix,
    )


def paginate_list(request, iterable, paginate_by=None, orphans=0):
    if not paginate_by:
        return iterable

    p = Paginator(iterable, paginate_by, orphans=orphans)
    page = request.GET.get("page")
    return p.get_page(p.num_pages if page == "last" else page)


def render_list(
    request,
    queryset,
    context=None,
    *,
    template_name_suffix="_list",
    paginate_by=None,
    orphans=0
):
    context = context or {}
    object_list = paginate_list(
        request, queryset, paginate_by=paginate_by, orphans=orphans
    )
    context.update(
        {
            "object_list": object_list,
            "%s_list" % queryset.model._meta.model_name: object_list,
        }
    )
    return render(request, template_name(queryset.model, template_name_suffix), context)


def render_detail(request, object, context=None, *, template_name_suffix="_detail"):
    context = context or {}
    context.update({"object": object, object._meta.model_name: object})
    return render(request, template_name(object, template_name_suffix), context)
