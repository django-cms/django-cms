from django.conf.urls.defaults import *
from cms import settings
from cms.views import details

urlpatterns = patterns('',
    # Public pages
    url(r'^$', details, {'slug':''}, name='pages-root'),
    url(r'^.*?/?(?P<slug>[-\w]+)/$', details, name='pages-details-by-slug'),
)

if settings.CMS_APPLICATIONS_URLS:
    """If there are some application urls, add special resolver, so we will
    have standard reverse support.
    """
    from cms.appresolver import DynamicAppRegexUrlResolver
    urlpatterns += (DynamicAppRegexUrlResolver(), )