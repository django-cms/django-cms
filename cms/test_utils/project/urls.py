from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from cms.utils.compat.dj import is_installed
from cms.utils.conf import get_cms_setting
from cms.test_utils.project.sampleapp.forms import LoginForm, LoginForm2, LoginForm3


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
                             url(r'^sample/login_other/$', 'django.contrib.auth.views.login',
                                 kwargs={'authentication_form': LoginForm2}),
                             url(r'^sample/login/$', 'django.contrib.auth.views.login',
                                 kwargs={'authentication_form': LoginForm}),
                             url(r'^sample/login3/$', 'django.contrib.auth.views.login',
                                 kwargs={'authentication_form': LoginForm3}),
                             url(r'^admin/', include(admin.site.urls)),
                             url(r'^example/$', 'cms.test_utils.project.placeholderapp.views.example_view'),
                             url(r'^plain_view/$', 'cms.test_utils.project.sampleapp.views.plain_view'),
                             url(r'^', include('cms.urls')),
)


if settings.DEBUG and is_installed('debug_toolbar'):
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
