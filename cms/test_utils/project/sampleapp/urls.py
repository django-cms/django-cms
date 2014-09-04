from django.conf.urls import patterns, url, include
from django.utils.translation import ugettext_lazy as _

"""
Also used in cms.tests.ApphooksTestCase
"""

urlpatterns = patterns('cms.test_utils.project.sampleapp.views',
    url(r'^$', 'sample_view', {'message': 'sample root page',}, name='sample-root'),
    url(r'^exempt/$', 'exempt_view', {'message': 'sample root page',}, name='sample-exempt'),
    url(r'^settings/$', 'sample_view', kwargs={'message': 'sample settings page'}, name='sample-settings'),
    url(r'^myparams/(?P<my_params>[\w_-]+)/$', 'sample_view', name='sample-params'),
    url(_(r'^account/$'), 'sample_view', {'message': 'sample account page'}, name='sample-account'),
    url(r'^account/my_profile/$', 'sample_view', {'message': 'sample my profile page'}, name='sample-profile'),
    url(r'^category/(?P<id>[0-9]+)/$', 'category_view', name='category_view'),
    url(r'^notfound/$', 'notfound', name='notfound'),
    url(r'^extra_1/$', 'extra_view', {'message': 'test urlconf'}, name='extra_first'),
    url(r'^', include('cms.test_utils.project.sampleapp.urls_extra'), {'opts': 'someopts'}),
)
