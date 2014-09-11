from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

"""
Also used in cms.tests.ApphooksTestCase
"""

urlpatterns = patterns('cms.test_utils.project.sampleapp.views',
    url(r'^current-app/$', 'current_app', name='current-app'),
    url(_('page'), 'current_app', name='translated-url'),
)
