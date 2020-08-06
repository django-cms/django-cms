from django.urls import re_path

from . import views
from .views import ClassDetail

urlpatterns = [
    re_path(r'^detail/(?P<pk>[0-9]+)/$', views.detail_view, name="example_detail"),
    re_path(r'^detail_char/(?P<pk>[a-z]+)/$', views.detail_view_char, name="example_detail_char"),
    re_path(r'^detail/class/(?P<pk>[0-9]+)/$', ClassDetail.as_view(), name="example_class_detail"),
    re_path(r'^$', views.list_view, name="example_list"),
]
