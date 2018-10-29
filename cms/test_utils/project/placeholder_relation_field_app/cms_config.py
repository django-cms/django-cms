from cms.app_base import CMSAppConfig

from .models import FancyPoll
from .views import render_fancy_poll


class FancyPollCMSAppConfig(CMSAppConfig):
    cms_enabled = True
    cms_toolbar_enabled_models = [(FancyPoll, render_fancy_poll)]
