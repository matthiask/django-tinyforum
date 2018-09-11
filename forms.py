from django import forms
from django.utils import timezone
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from ckeditor.fields import RichTextFormField
from tinyforum import signals
from tinyforum.models import Thread, Post, PostReport


class BaseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.authored_by_id:
            instance.authored_by = self.request.user
        if commit:
            instance.save()
        return instance


class CreateThreadForm(BaseForm, forms.ModelForm):
    text = RichTextFormField(
        label=_('text'),
        config_name='tinyforum-post',
        extra_plugins=['emojione'],
        external_plugin_resources=[(
            'emojione',
            '/static/webapp/lib/ckeditor-emojione-1.0.1/',
            'plugin.js',
        )],
    )

    class Meta:
        model = Thread
        fields = ('title',)

    def save(self):
        instance = super().save()
        instance.starred_by.add(self.request.user)
        instance.posts.create(
            authored_by=instance.authored_by,
            text=self.cleaned_data["text"],
        )
        return instance


class UpdateThreadForm(BaseForm, forms.ModelForm):
    class Meta:
        model = Thread
        fields = ('title',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.closed_at:
            self.fields['close_thread'] = forms.BooleanField(
                label=_('Close thread'),
                required=False,
                help_text=_(
                    'The thread will still be visible, but no posts'
                    ' can be added to it.'
                ),
            )

    def save(self):
        instance = super().save(commit=False)
        if self.cleaned_data.get('close_thread'):
            instance.closed_at = timezone.now()
        instance.save()
        return instance


class ModerateThreadForm(UpdateThreadForm, forms.ModelForm):
    moderation_status = forms.ChoiceField(
        label=capfirst(_('moderation status')),
        choices=PostReport.MODERATION_STATUS_CHOICES,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Thread
        fields = ('title', 'is_pinned', 'moderation_status')


def form_for_thread(request, *, instance=None, moderation=False):
    kw = {
        'data': request.POST if request.method == 'POST' else None,
        'request': request,
        'instance': instance,
    }
    if instance is None:
        return CreateThreadForm(**kw)
    elif moderation:
        return ModerateThreadForm(**kw)
    elif instance and request.user == instance.authored_by:
        return UpdateThreadForm(**kw)
    return None


class BasePostForm(BaseForm):
    def __init__(self, *args, **kwargs):
        self.thread = kwargs.pop('thread')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.thread_id:
            instance.thread = self.thread
        if commit:
            instance.save()
        return instance


class CreatePostForm(BasePostForm, forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text',)

    def save(self):
        instance = super().save()
        signals.post_created.send(
            sender=Post,
            instance=instance,
            form=self,
            request=self.request,
        )
        return instance


class UpdatePostForm(BasePostForm, forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text',)


class ModeratePostForm(BasePostForm, forms.ModelForm):
    moderation_status = forms.ChoiceField(
        label=capfirst(_('moderation status')),
        choices=PostReport.MODERATION_STATUS_CHOICES,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Post
        fields = ('text', 'moderation_status')


def form_for_post(request, *, thread, instance=None, moderation=False):
    kw = {
        'data': request.POST if request.method == 'POST' else None,
        'request': request,
        'instance': instance,
        'thread': thread,
    }
    if thread.closed_at:
        return None
    elif moderation:
        return ModeratePostForm(**kw)
    elif instance and request.user == instance.authored_by:
        return UpdatePostForm(**kw)
    elif instance is None:
        return CreatePostForm(**kw)
    return None


class CreatePostReportForm(BaseForm, forms.ModelForm):
    reason = forms.ChoiceField(
        label=capfirst(_('reason')),
        choices=PostReport.REASON_CHOICES,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = PostReport
        fields = ('reason', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.post = kwargs.pop('post')
        super().__init__(*args, **kwargs)

    def save(self):
        instance = super().save(commit=False)
        instance.post = self.post
        instance.save()
        return instance


class HandlePostReportForm(BaseForm, forms.ModelForm):
    moderation_status = forms.ChoiceField(
        label=capfirst(_('moderation status')),
        choices=PostReport.MODERATION_STATUS_CHOICES,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = PostReport
        fields = ('moderation_status',)

    def save(self):
        instance = super().save(commit=False)
        instance.handled_at = timezone.now()
        instance.handled_by = self.request.user
        instance.save()
        instance.post.moderation_status = instance.moderation_status
        instance.post.save()
        signals.post_report_handled.send(
            sender=PostReport,
            instance=instance,
            form=self,
            request=self.request,
        )
        return instance
