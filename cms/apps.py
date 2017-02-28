from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from cms.utils.setup import setup


class CMSConfig(AppConfig):
    name = 'cms'
    verbose_name = _("django CMS")

    def ready(self):
        setup()
