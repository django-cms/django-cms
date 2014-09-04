from django.conf.urls import patterns, url, include

"""
Used in test_apphook_excluded_permissions
"""

urlpatterns = patterns('cms.test_utils.project.sampleapp.views',
    url(r'^excluded/',
        include('cms.test_utils.project.sampleapp.urls_example', namespace="excluded", app_name='some_app')),
    url(r'^not_excluded/',
        include('cms.test_utils.project.sampleapp.urls_example', namespace="not_excluded", app_name='some_app')),
)
