from django.conf.urls import *
try:
    from django.conf.urls.i18n import i18n_patterns
except ImportError:
    from i18nurls.i18n import i18n_patterns

urlpatterns = patterns('cms.test_utils.project.placeholderapp.views',
    url(r'^detail/(?P<id>[0-9]+)/$', 'detail_view_multi', name="detail_multi"),
    url(r'^$', 'list_view_multi', name="list_multi"),
)
