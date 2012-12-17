from django.conf.urls.defaults import *
from django.utils.translation import ugettext_lazy as _

"""
Also used in cms.tests.ApphooksTestCase
"""

urlpatterns = patterns('cms.test_utils.project.sampleapp.views',
    url(r'^$', 'sample_view', {'message': 'sample apphook2 root page',}, name='sample2-root'),
)
