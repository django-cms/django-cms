from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, re_path
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve

from cms.test_utils.project.placeholder_relation_field_app.views import (
    detail as fancy_poll_detail_view,
)
from cms.test_utils.project.placeholderapp.views import (
    example_view,
    latest_view,
)
from cms.test_utils.project.sampleapp.forms import (
    LoginForm,
    LoginForm2,
    LoginForm3,
)
from cms.test_utils.project.sampleapp.views import plain_view
from cms.utils.conf import get_cms_setting

admin.autodiscover()

urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    re_path(
        r'^media/cms/(?P<path>.*)$', serve, {'document_root': get_cms_setting('MEDIA_ROOT'), 'show_indexes': True}
    ),
    re_path(r'^jsi18n/(?P<packages>\S+?)/$', JavaScriptCatalog.as_view()),
]

urlpatterns += staticfiles_urlpatterns()


urlpatterns += i18n_patterns(
    re_path(r'^sample/login_other/$', LoginView.as_view(), kwargs={'authentication_form': LoginForm2}),
    re_path(r'^sample/login/$', LoginView.as_view(), kwargs={'authentication_form': LoginForm}),
    re_path(r'^sample/login3/$', LoginView.as_view(), kwargs={'authentication_form': LoginForm3}),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^example/$', example_view),
    re_path(r'^example/latest/$', latest_view),
    re_path(r'^plain_view/$', plain_view),
    re_path(r'^fancypolls/detail/([0-9]+)/$', fancy_poll_detail_view, name='fancy_poll_detail_view'),
    re_path(r'^', include('cms.urls')),
)
