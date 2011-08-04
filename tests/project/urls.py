from django.conf import settings
from django.conf.urls.defaults import handler500, handler404, patterns, include, \
    url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^example/$', 'project.placeholderapp.views.example_view'),
    url(r'^jsi18n/(?P<packages>\S+?)/$', 'django.views.i18n.javascript_catalog'),
    url(r'^media/cms/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.CMS_MEDIA_ROOT, 'show_indexes': True}),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    (r'', include('staticfiles.urls')),
    url(r'^', include('cms.urls')),
)
