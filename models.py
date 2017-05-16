from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ckeditor.fields import RichTextField
from html_sanitizer.django import get_sanitizer


class BaseQuerySet(models.QuerySet):
    def visible(self):
        return self.exclude(moderation_status=self.model.HIDDEN)


class BaseModel(models.Model):
    GOOD = 'good'
    FLAGGED = 'flagged'
    COLLAPSED = 'collapsed'
    HIDDEN = 'hidden'
    MODERATION_STATUS_CHOICES = (
        (GOOD, _('good')),
        (FLAGGED, _('flagged')),
        (COLLAPSED, _('collapsed')),
        (HIDDEN, _('hidden')),
    )

    created_at = models.DateTimeField(
        _('created at'),
        default=timezone.now,
    )
    authored_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('authored by'),
    )
    moderation_status = models.CharField(
        _('moderation status'),
        max_length=10,
        choices=MODERATION_STATUS_CHOICES,
    )

    objects = BaseQuerySet.as_manager()

    class Meta:
        abstract = True


class Thread(BaseModel):
    title = models.CharField(
        _('title'),
        max_length=200,
    )
    is_pinned = models.BooleanField(
        _('is pinned'),
        default=False,
    )
    closed_at = models.DateTimeField(
        _('closed at'),
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = _('thread')
        verbose_name_plural = _('threads')

    def __str__(self):
        return self.title


class Post(BaseModel):
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        verbose_name=_('thread'),
    )
    text = RichTextField(
        _('text'),
        config_name='tinyforum-post',
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = _('post')
        verbose_name_plural = _('post')

    def clean(self):
        super().clean()
        self.text = get_sanitizer('tinyforum-post').sanitize(self.text)
