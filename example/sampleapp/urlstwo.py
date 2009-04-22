from django.conf.urls.defaults import *

urlpatterns = patterns('sampleapp.views',
    (r'^$', 'sample_view', {'message': 'urlstwo.py => root'}),
    (r'^sublevel/$', 'sample_view', {'message': 'urlstwo.py => sublevel'}),
)
