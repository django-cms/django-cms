from django.conf.urls import url, include

urlpatterns = [
    url(r'^excluded/',
        include('cms.test_utils.project.sampleapp.urls_example', namespace="excluded", app_name='some_app')),
    url(r'^not_excluded/',
        include('cms.test_utils.project.sampleapp.urls_example', namespace="not_excluded", app_name='some_app')),
]
