from django.conf.urls.defaults import *

urlpatterns = patterns('sampleapp.views',
    (r'^$', 'sample_view', {'message': 'urlstwo.py => root'}),
    url(r'^sublevel/$', 'sample_view', {'message': 'urlstwo.py => sublevel1'}, name='sample-app-sublevel'),
    url(r'^sublevel2/$', 'sample_view', {'message': 'urlstwo.py => sublevel2'}, name='sample-app-sublevel2'),
    url(r'^sublevel/sublevel3/$', 'sample_view', {'message': 'urlstwo.py => sublevel3'}, name='sample-app-sublevel3'),
)
