from django.conf.urls import *

"""
Also used in cms.tests.ApphooksTestCase
"""

urlpatterns = patterns('cms.test_utils.project.sampleapp.views',
    url(r'^current-app/$', 'current_app', name='current-app' ),
)
