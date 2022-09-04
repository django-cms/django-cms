from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^$', views.sample_view, {'message': 'sample root page',}, name='sample-config-root'),
]
