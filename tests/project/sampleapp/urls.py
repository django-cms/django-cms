from django.conf.urls.defaults import *

"""
Also used in cms.tests.ApphooksTestCase
"""

urlpatterns = patterns('project.sampleapp.views',
    url(r'^$', 'sample_view', {'message': 'sample root page',}, name='sample-root'),  
    url(r'^settings/$', 'sample_view', kwargs={'message': 'sample settings page'}, name='sample-settings'),
    url(r'^account/$', 'sample_view', {'message': 'sample account page'}, name='sample-account'),
    url(r'^account/my_profile/$', 'sample_view', {'message': 'sample my profile page'}, name='sample-profile'),
    url(r'(?P<id>[0-9]+)/$', 'category_view', name='category_view'),
    url(r'notfound/$', 'notfound', name='notfound'),
)
