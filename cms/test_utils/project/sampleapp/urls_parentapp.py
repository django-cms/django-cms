from django.urls import re_path

from cms.test_utils.project.sampleapp import views

urlpatterns = [
    re_path(r'^(?P<path>.+)$', views.parentapp_view, name='parentapp_view'),
]
