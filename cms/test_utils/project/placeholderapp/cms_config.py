from cms.app_base import CMSAppConfig

from .models import Example1
from .views import render_example_content


class Example1CMSAppConfig(CMSAppConfig):
    cms_enabled = True
    cms_toolbar_enabled_models = [(Example1, render_example_content)]
