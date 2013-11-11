from django.conf.urls import *

urlpatterns = patterns('cms.test_utils.project.placeholderapp.views',
    url(r'^detail/(?P<id>[0-9]+)/$', 'detail_view', name="detail"),
    url(r'^$', 'list_view', name="list"),
)
