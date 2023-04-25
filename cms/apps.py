from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CMSConfig(AppConfig):
    name = 'cms'
    verbose_name = _("django CMS")
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from cms.utils.setup import setup

        setup()
