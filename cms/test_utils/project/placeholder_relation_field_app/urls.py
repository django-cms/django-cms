from django.urls import re_path

from .views import detail

urlpatterns = [
    re_path(r'^detail/([0-9]+)/$', detail, name='detail_view'),
]
