from django.contrib import admin

from tinyforum import models


@admin.register(models.Thread)
class ThreadAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'title', 'is_pinned', 'authored_by', 'created_at', 'closed_at',
        'moderation_status'
    )
    list_filter = ('is_pinned', 'moderation_status')
    radio_fields = {'moderation_status': admin.HORIZONTAL}
    filter_horizontal = ('starred_by',)
    raw_id_fields = ('authored_by', 'latest_post')
    search_fields = ('title',)


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        '__str__', 'authored_by', 'thread', 'created_at', 'moderation_status',
    )
    list_filter = ('moderation_status',)
    ordering = ['-created_at']
    radio_fields = {'moderation_status': admin.HORIZONTAL}
    raw_id_fields = ('thread', 'authored_by')
    search_fields = ('thread__title', 'text')


@admin.register(models.PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = (
        'post', 'reason', 'notes', 'handled_at', 'handled_by',
        'moderation_status',
    )
    list_filter = ('reason', 'handled_at')
    raw_id_fields = ('authored_by', 'handled_by', 'post')
