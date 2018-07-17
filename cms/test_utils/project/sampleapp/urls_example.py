# -*- coding: utf-8 -*-
from django.conf.urls import url

from ..placeholderapp import views

app_name = 'example_app'

urlpatterns = [
    url(r'^example/$', views.example_view, name="example"),
]
