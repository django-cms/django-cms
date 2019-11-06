from django.conf.urls import url, include

urlpatterns = [
    url(r'^excluded/',
        include('cms.test_utils.project.sampleapp.urls_example', namespace="excluded")),
    url(r'^not_excluded/',
        include('cms.test_utils.project.sampleapp.urls_example', namespace="not_excluded")),
]
