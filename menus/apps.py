from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class MenusConfig(AppConfig):
    name = 'menus'
    verbose_name = _("django CMS menus system")
