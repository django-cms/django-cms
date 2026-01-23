from django.conf import settings
from django.urls import include, path, re_path
from django.urls.resolvers import RegexPattern

from cms import views
from cms.appresolver import LazyURLResolver
from cms.constants import SLUG_REGEXP

if settings.APPEND_SLASH:
    regexp = r'^(?P<slug>%s)/$' % SLUG_REGEXP
else:
    regexp = r'^(?P<slug>%s)$' % SLUG_REGEXP


def _get_apphook_urlpatterns():
    # Avoid touching the DB / apphooks at import time.
    from cms.apphook_pool import apphook_pool

    if not apphook_pool.get_apphooks():
        return []

    from cms.appresolver import get_app_patterns

    return get_app_patterns()


urlpatterns = [
    # If there are some application urls, use special resolver,
    # so we will have standard reverse support.
    LazyURLResolver(RegexPattern(r''), 'app_resolver', get_urlpatterns=_get_apphook_urlpatterns),
    path('cms_login/', views.login, name='cms_login'),
    path('cms_wizard/', include('cms.wizards.urls')),
    re_path(regexp, views.details, name='pages-details-by-slug'),
    path('', views.details, {'slug': ''}, name='pages-root'),
]
