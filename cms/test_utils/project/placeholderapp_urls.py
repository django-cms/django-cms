from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, re_path
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve

from cms.test_utils.project.placeholderapp.views import detail_view
from cms.utils.conf import get_cms_setting

admin.autodiscover()

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    re_path(r'^media/cms/(?P<path>.*)$', serve,
            {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}),
    re_path(r'^jsi18n/(?P<packages>\S+?)/$', JavaScriptCatalog.as_view()),
]

urlpatterns += i18n_patterns(
    re_path(r'^detail/(?P<id>[0-9]+)/$', detail_view, name="detail"),
    re_path(r'^detail/(?P<pk>[0-9]+)/$', detail_view, name="example_detail"),
    re_path(r'^', include('cms.urls')),
)
