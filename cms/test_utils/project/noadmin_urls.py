from django.conf import settings
from django.urls import include, re_path
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve

from cms.utils.conf import get_cms_setting

urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    re_path(r'^media/cms/(?P<path>.*)$', serve,
            {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}),
    re_path(r'^jsi18n/(?P<packages>\S+?)/$', JavaScriptCatalog.as_view()),
    re_path(r'^', include('cms.urls')),
]
