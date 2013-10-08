# -*- coding: utf-8 -*-
from cms.compat import get_user_model
from cms.compat import user_model_label
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from cms.utils.compat.dj import force_unicode, python_2_unicode_compatible


@python_2_unicode_compatible
class UserSettings(models.Model):
    user = models.ForeignKey(user_model_label, editable=False)
    language = models.CharField(_("Language"), max_length=10, choices=settings.LANGUAGES,
                                help_text=_("The language for the admin interface and toolbar"))
    clipboard = models.ForeignKey('cms.Placeholder', blank=True, null=True, editable=False)

    class Meta:
        verbose_name = _('user setting')
        verbose_name_plural = _('user settings')
        app_label = 'cms'

    def __str__(self):
        return force_unicode(self.user)


