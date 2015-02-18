from cms.utils.compat.dj import is_installed
from cms.utils.conf import get_cms_setting
from django.conf import settings
from django.conf.urls import patterns, include, \
    url
from django.contrib import admin

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

urlpatterns = patterns('',
                       #(r'', include('django.contrib.staticfiles.urls')),
                       url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
                           {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                       url(r'^media/cms/(?P<path>.*)$', 'django.views.static.serve',
                           {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}),
                       url(r'^jsi18n/(?P<packages>\S+?)/$', 'django.views.i18n.javascript_catalog'),

)

urlpatterns += staticfiles_urlpatterns()

urlpatterns += patterns('',
                        url(r'^admin/', include(admin.site.urls)),
                        url(r'^example/$', 'cms.test_utils.project.placeholderapp.views.example_view'),
                        url(r'^', include('cms.urls')),
)


if settings.DEBUG and is_installed('debug_toolbar'):
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
