from django.conf.urls.defaults import *

"""
Also used in cms.tests.ApphooksTestCase
"""

urlpatterns = patterns('cms.test_utils.project.sampleapp.views',
    url(r'extra_2/$', 'extra_view', {'message': 'test included urlconf'}, name='extra_second'),
)
