from cms.utils.conf import get_cms_setting
from django.conf import settings
from django.conf.urls.defaults import handler500, handler404, patterns, include, \
    url
from django.contrib import admin
try:
    from django.conf.urls.i18n import i18n_patterns
except ImportError:
    from i18nurls.i18n import i18n_patterns

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

urlpatterns += i18n_patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^example/$', 'cms.test_utils.project.placeholderapp.views.example_view'),
    url(r'^', include('cms.urls')),
)
