# -*- coding: utf-8 -*-
from django.conf.urls import url

from ..placeholderapp import views

urlpatterns = [
    url(r'^example/$', views.example_view, name="example"),
]
