from django.urls import path
from django.urls import include

urlpatterns = [
    path('excluded/',
            include('cms.test_utils.project.sampleapp.urls_example', namespace="excluded")),
    path('not_excluded/',
            include('cms.test_utils.project.sampleapp.urls_example', namespace="not_excluded")),
]
