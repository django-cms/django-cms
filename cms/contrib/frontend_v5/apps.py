from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FrontendV5Config(AppConfig):
    name = 'cms.contrib.frontend_v5'
    label = 'cms_frontend_v5'
    verbose_name = _("django CMS Frontend v5")
    default_auto_field = 'django.db.models.AutoField'
