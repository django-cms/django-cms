import uuid
from django.db import models
from cms.models.fields import PlaceholderField
from django.utils.translation import ugettext_lazy as _
from cms.models.pluginmodel import CMSPlugin


class Stack(models.Model):
    name = models.CharField(
        verbose_name=_(u'stack name'), max_length=255, blank=True, default='',
        help_text=_(u'Descriptive name to identify this stack. Not displayed to users.'))
    code = models.CharField(
        verbose_name=_(u'stack code'), max_length=255, unique=True, blank=True,
        help_text=_(u'To render the stack in templates.'))
    content = PlaceholderField(
        slotname=u'stack_content', verbose_name=_(u'stack content'), related_name='stacks_contents')

    class Meta:
        verbose_name = _(u'stack')
        verbose_name_plural = _(u'stacks')

    def __unicode__(self):
        return self.name

    def clean(self):
        # TODO: check for clashes if the random code is already taken
        if not self.code:
            self.code = u'stack-%s' % uuid.uuid4()


class StackLink(CMSPlugin):
    stack = models.ForeignKey(Stack, verbose_name=_(u'stack'))

    def __unicode__(self):
        return self.stack.name
