# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns

urlpatterns = patterns(
    '',
    url(r'^example/$', 'cms.test_utils.project.placeholderapp.views.example_view', name="example"),
)
