from django.conf import settings
from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _


class PlaceholderForeignKey(models.ForeignKey):
    def run_checks(self, placeholder, user):
        # A clipboard is private to its owner: only they have permission to
        # change it. Other users must not be able to read from or write to it.
        try:
            return placeholder.source.has_placeholder_change_permission(user)
        except AttributeError:
            return False


class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        editable=False,
        related_name='djangocms_usersettings',
    )
    language = models.CharField(_("Language"), max_length=10, choices=settings.LANGUAGES,
                                help_text=_("The language for the admin interface and toolbar"))
    clipboard = PlaceholderForeignKey(
        'cms.Placeholder',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        editable=False,
    )

    class Meta:
        verbose_name = _('user setting')
        verbose_name_plural = _('user settings')
        app_label = 'cms'

    def __str__(self):
        return force_str(self.user)

    def has_placeholder_change_permission(self, user):
        # User always has permission to change their own clipboard, but only
        # their own: a clipboard may contain content other users are not
        # allowed to see.
        return self.user_id == user.pk or user.is_superuser
