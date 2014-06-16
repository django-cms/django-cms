from django.conf.urls import patterns, url

urlpatterns = patterns('cms.test_utils.project.placeholderapp.views',
    url(r'^detail/(?P<pk>[0-9]+)/$', 'detail_view_multi', name="detail_multi"),
    url(r'^$', 'list_view_multi', name="list_multi"),
)
