import uuid

from django.contrib.auth import get_permission_codename
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from cms.models.fields import PlaceholderField
from cms.utils.copy_plugins import copy_plugins_to


def static_slotname(instance):
    """
    Returns a string to be used as the slot
    for the static placeholder field.
    """
    return instance.code


@python_2_unicode_compatible
class StaticPlaceholder(models.Model):
    CREATION_BY_TEMPLATE = 'template'
    CREATION_BY_CODE = 'code'
    CREATION_METHODS = (
        (CREATION_BY_TEMPLATE, _('by template')),
        (CREATION_BY_CODE, _('by code')),
    )
    name = models.CharField(
        verbose_name=_(u'static placeholder name'), max_length=255, blank=True, default='',
        help_text=_(u'Descriptive name to identify this static placeholder. Not displayed to users.'))
    code = models.CharField(
        verbose_name=_(u'placeholder code'), max_length=255, blank=True,
        help_text=_(u'To render the static placeholder in templates.'))
    draft = PlaceholderField(static_slotname, verbose_name=_(u'placeholder content'), related_name='static_draft')
    public = PlaceholderField(static_slotname, editable=False, related_name='static_public')
    dirty = models.BooleanField(default=False, editable=False)
    creation_method = models.CharField(
        verbose_name=_('creation_method'), choices=CREATION_METHODS,
        default=CREATION_BY_CODE, max_length=20, blank=True,
    )
    site = models.ForeignKey(Site, null=True, blank=True)

    class Meta:
        verbose_name = _(u'static placeholder')
        verbose_name_plural = _(u'static placeholders')
        app_label = 'cms'
        unique_together = (('code', 'site'),)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return self.name or self.code or six.text_type(self.pk)
    get_name.short_description = _(u'static placeholder name')

    def clean(self):
        # TODO: check for clashes if the random code is already taken
        if not self.code:
            self.code = u'static-%s' % uuid.uuid4()
        if not self.site:
            placeholders = StaticPlaceholder.objects.filter(code=self.code, site__isnull=True)
            if self.pk:
                placeholders = placeholders.exclude(pk=self.pk)
            if placeholders.exists():
                raise ValidationError(_("A static placeholder with the same site and code already exists"))

    def publish(self, request, language, force=False):
        if force or self.has_publish_permission(request):
            self.public.clear(language=language)
            plugins = self.draft.get_plugins_list(language=language)
            copy_plugins_to(plugins, self.public, no_signals=True)
            self.dirty = False
            self.save()
            return True
        return False

    def has_change_permission(self, request):
        if request.user.is_superuser:
            return True
        opts = self._meta
        return request.user.has_perm(opts.app_label + '.' + get_permission_codename('change', opts))

    def has_publish_permission(self, request):
        if request.user.is_superuser:
            return True
        opts = self._meta
        return request.user.has_perm(opts.app_label + '.' + get_permission_codename('change', opts)) and \
               request.user.has_perm(opts.app_label + '.' + 'publish_page')
