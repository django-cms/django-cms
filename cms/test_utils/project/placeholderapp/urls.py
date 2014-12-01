from django.conf.urls import patterns, url
from .views import ClassDetail

urlpatterns = patterns('cms.test_utils.project.placeholderapp.views',
    url(r'^detail/(?P<pk>[0-9]+)/$', 'detail_view', name="example_detail"),
    url(r'^detail_char/(?P<pk>[a-z]+)/$', 'detail_view_char', name="example_detail_char"),
    url(r'^detail/class/(?P<pk>[0-9]+)/$', ClassDetail.as_view(), name="example_class_detail"),
    url(r'^$', 'list_view', name="example_list"),
)
