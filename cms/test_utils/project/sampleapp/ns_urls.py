from django.urls import re_path
from django.utils.translation import gettext_lazy as _

from . import views

urlpatterns = [
    re_path(r'^current-app/$', views.current_app, name='current-app'),
    re_path(_('page'), views.current_app, name='translated-url'),
]
