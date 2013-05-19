# -*- coding: utf-8 -*-
from cms.compat import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class UserSettings(models.Model):
    user = models.ForeignKey(User, editable=False)
    language = models.CharField(_("Language"), max_length=10, choices=settings.LANGUAGES,
                                help_text=_("The language for the admin interface and toolbar"))
    clipboard = models.ForeignKey('cms.Placeholder', blank=True, null=True, editable=False)

    class Meta:
        verbose_name = _('user setting')
        verbose_name_plural = _('user settings')
        app_label = 'cms'

    def __unicode__(self):
        return unicode(self.user)


