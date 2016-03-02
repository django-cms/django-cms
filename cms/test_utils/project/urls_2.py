
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import javascript_catalog
from django.views.static import serve

from cms.test_utils.project.placeholderapp.views import example_view
from cms.utils.compat import DJANGO_1_7
from cms.utils.conf import get_cms_setting

admin.autodiscover()

urlpatterns = [
    url(r'^media/(?P<path>.*)$', serve,
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'^media/cms/(?P<path>.*)$', serve,
        {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}),
    url(r'^jsi18n/(?P<packages>\S+?)/$', javascript_catalog),
]

urlpatterns += staticfiles_urlpatterns()


if DJANGO_1_7:
    urlpatterns += i18n_patterns('',
        url(r'^admin/', include(admin.site.urls)),
        url(r'^example/$', example_view),
        url(r'^', include('cms.urls')),
    )
else:
    urlpatterns += i18n_patterns(
        url(r'^admin/', include(admin.site.urls)),
        url(r'^example/$', example_view),
        url(r'^', include('cms.urls')),
    )


if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
