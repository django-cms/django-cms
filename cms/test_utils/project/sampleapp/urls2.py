from django.conf.urls import patterns, url

"""
Also used in cms.tests.ApphooksTestCase
"""

urlpatterns = patterns('cms.test_utils.project.sampleapp.views',
                       url(r'^$', 'sample_view', {'message': 'sample apphook2 root page', }, name='sample2-root'),
)
