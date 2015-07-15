from django.conf.urls import url

from . import views
from .views import ClassDetail

urlpatterns = [
    url(r'^detail/(?P<pk>[0-9]+)/$', views.detail_view, name="example_detail"),
    url(r'^detail_char/(?P<pk>[a-z]+)/$', views.detail_view_char, name="example_detail_char"),
    url(r'^detail/class/(?P<pk>[0-9]+)/$', ClassDetail.as_view(), name="example_class_detail"),
    url(r'^$', views.list_view, name="example_list"),
]
