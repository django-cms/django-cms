from django.urls import include, re_path

urlpatterns = [
    re_path(r'^excluded/',
            include('cms.test_utils.project.sampleapp.urls_example', namespace="excluded")),
    re_path(r'^not_excluded/',
            include('cms.test_utils.project.sampleapp.urls_example', namespace="not_excluded")),
]
