from django.views.i18n import javascript_catalog
from django.views.static import serve

from cms.test_utils.project.placeholderapp.views import example_view
from cms.utils import get_cms_setting
from cms.utils.compat import DJANGO_1_7
from cms.utils.compat.dj import is_installed
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'^media/(?P<path>.*)$', serve,
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'^media/cms/(?P<path>.*)$', serve,
        {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}),
    url(r'^jsi18n/(?P<packages>\S+?)/$', javascript_catalog),
]

if DJANGO_1_7:
    urlpatterns += i18n_patterns('',
        url(r'^admin/', include(admin.site.urls)),
        url(r'^content/', include('cms.urls')),
        url(r'^example/$', example_view, name='example_view'),
    )

else:
    urlpatterns += i18n_patterns(
        url(r'^admin/', include(admin.site.urls)),
        url(r'^content/', include('cms.urls')),
        url(r'^example/$', example_view, name='example_view'),
    )


if settings.DEBUG and is_installed('debug_toolbar'):
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
