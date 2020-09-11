from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^$', views.sample_view, {'message': 'sample apphook2 root page', }, name='sample2-root'),
]
