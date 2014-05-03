from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CMSConfig(AppConfig):
    name = 'cms'
    verbose_name = _("django CMS")

    def ready(self):
        from cms.models import validate_dependencies, validate_settings
        validate_dependencies()
        validate_settings()