from django.conf.urls.defaults import *

urlpatterns = patterns('sampleapp.views',
    (r'^$', 'sample_view', {'message': 'urls.py => root (DE)',}),
    (r'^$', 'sample_view', {'message': 'urls.py => root (EN)'}),
    
    url(r'^sublevel/$', 'sample_view', kwargs={'message': 'urls.py => sublevel'}, name='sample-app-sublevel'),
)
