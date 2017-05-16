from django.contrib import admin

from tinyforum import models


@admin.register(models.Thread)
class ThreadAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'title', 'is_pinned', 'created_at', 'closed_at', 'moderation_status')
    list_filter = ('is_pinned', 'moderation_status')
    search_fields = ('title',)


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'created_at', 'moderation_status',
    )
    list_filter = ('moderation_status',)
    search_fields = ('thread__title', 'text')
