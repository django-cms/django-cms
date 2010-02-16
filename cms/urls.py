from django.conf.urls.defaults import *
from django.conf import settings
from cms.views import details

if settings.APPEND_SLASH:
    reg = url(r'^(?P<slug>[0-9A-Za-z-_.//]+)/$', details, name='pages-details-by-slug')
else:
    reg = url(r'^(?P<slug>[0-9A-Za-z-_.//]+)$', details, name='pages-details-by-slug')

urlpatterns = [
    # Public pages
    url(r'^$', details, {'slug':''}, name='pages-root'),
    reg,
]

if settings.CMS_APPLICATIONS_URLS:
    """If there are some application urls, add special resolver, so we will
    have standard reverse support.
    """
    from cms.appresolver import get_app_patterns
    urlpatterns = get_app_patterns() + urlpatterns
    #urlpatterns = (dynamic_app_regex_url_resolver, ) + urlpatterns
    
urlpatterns = patterns('', *urlpatterns)