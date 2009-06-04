from django.conf.urls.defaults import *
from cms import settings
from cms.views import details

urlpatterns = (
    # Public pages
    url(r'^$', details, {'slug':''}, name='pages-root'),
    url(r'^(?P<slug>[0-9A-Za-z-_//]+)/$', details, name='pages-details-by-slug'),
)

if settings.CMS_APPLICATIONS_URLS:
    """If there are some application urls, add special resolver, so we will
    have standard reverse support.
    """
    from cms.appresolver import dynamic_app_regex_url_resolver
    urlpatterns = (dynamic_app_regex_url_resolver, ) + urlpatterns
    
urlpatterns = patterns('', *urlpatterns)