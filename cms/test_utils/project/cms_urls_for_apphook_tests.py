from cms.apphook_pool import apphook_pool
from cms.utils.compat.dj import is_installed
from cms.views import details
from django.conf import settings
from django.conf.urls import url, include

if settings.APPEND_SLASH:
    reg = url(r'^(?P<slug>[0-9A-Za-z-_.//]+)/$', details, name='pages-details-by-slug')
else:
    reg = url(r'^(?P<slug>[0-9A-Za-z-_.//]+)$', details, name='pages-details-by-slug')

urlpatterns = [
    # Public pages
    url(r'^$', details, {'slug':''}, name='pages-root'),
    reg,
]

if apphook_pool.get_apphooks():
    """If there are some application urls, add special resolver, so we will
    have standard reverse support.
    """
    from cms.appresolver import get_app_patterns
    urlpatterns = get_app_patterns() + urlpatterns

if settings.DEBUG and is_installed('debug_toolbar'):
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
