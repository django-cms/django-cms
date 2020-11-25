from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, re_path
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve

from cms.test_utils.project.placeholderapp.views import example_view
from cms.utils.conf import get_cms_setting

admin.autodiscover()

urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    re_path(r'^media/cms/(?P<path>.*)$', serve,
            {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}),
    re_path(r'^jsi18n/(?P<packages>\S+?)/$', JavaScriptCatalog.as_view()),
]

urlpatterns += staticfiles_urlpatterns()

urlpatterns += [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^example/$', example_view),
    re_path(r'^', include('cms.urls')),
]
