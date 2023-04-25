from django.conf import settings
from django.urls import include, re_path

from cms.apphook_pool import apphook_pool
from cms.views import details

if settings.APPEND_SLASH:
    reg = re_path(r'^(?P<slug>[0-9A-Za-z-_.//]+)/$', details, name='pages-details-by-slug')
else:
    reg = re_path(r'^(?P<slug>[0-9A-Za-z-_.//]+)$', details, name='pages-details-by-slug')

urlpatterns = [
    # Public pages
    re_path(r'^example/',
            include('cms.test_utils.project.sampleapp.urls_example', namespace="example1")),
    re_path(r'^example2/',
            include('cms.test_utils.project.sampleapp.urls_example', namespace="example2")),
    re_path(r'^$', details, {'slug': ''}, name='pages-root'),
    reg,
]

if apphook_pool.get_apphooks():
    """If there are some application urls, add special resolver, so we will
    have standard reverse support.
    """
    from cms.appresolver import get_app_patterns
    urlpatterns = get_app_patterns() + urlpatterns
