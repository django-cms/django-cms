from django.conf import settings
from django.urls import include, path, re_path

from cms import views
from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_patterns
from cms.constants import SLUG_REGEXP

if settings.APPEND_SLASH:
    regexp = r'^(?P<slug>%s)/$' % SLUG_REGEXP
else:
    regexp = r'^(?P<slug>%s)$' % SLUG_REGEXP

if apphook_pool.get_apphooks():
    # If there are some application urls, use special resolver,
    # so we will have standard reverse support.
    urlpatterns = get_app_patterns()
else:
    urlpatterns = []


urlpatterns.extend([
    path('cms_login/', views.login, name='cms_login'),
    path('cms_wizard/', include('cms.wizards.urls')),
    re_path(regexp, views.details, name='pages-details-by-slug'),
    path('', views.details, {'slug': ''}, name='pages-root'),
])
