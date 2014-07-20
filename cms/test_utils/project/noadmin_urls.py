from cms.utils.compat.dj import is_installed
from cms.utils.conf import get_cms_setting
from django.conf import settings
from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^jsi18n/(?P<packages>\S+?)/$', 'django.views.i18n.javascript_catalog'),
    url(r'^media/cms/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'^', include('cms.urls')),
)


if settings.DEBUG and is_installed('debug_toolbar'):
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
