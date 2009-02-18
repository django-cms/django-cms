from django.conf.urls.defaults import *
from cms.views import details

urlpatterns = patterns('',
    # Public pages
    url(r'^$', details, {'slug':''}, name='pages-root'),
    url(r'^.*?/?(?P<slug>[-\w]+)/$', details, name='pages-details-by-slug'),
)
