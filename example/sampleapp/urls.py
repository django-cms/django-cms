from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse

urlpatterns = patterns('sampleapp.views',
    (r'^$', 'sample_view', {'message': 'urls.py => root (DE)', '_lang': 'de'}),
    (r'^$', 'sample_view', {'message': 'urls.py => root (EN)', '_lang': 'en'}),
    
    (r'^sublevel/$', 'sample_view', {'message': 'urls.py => sublevel'}),
)
