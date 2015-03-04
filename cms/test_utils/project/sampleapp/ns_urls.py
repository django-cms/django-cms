from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _

from . import views

urlpatterns = [
    url(r'^current-app/$', views.current_app, name='current-app'),
    url(_('page'), views.current_app, name='translated-url'),
]
