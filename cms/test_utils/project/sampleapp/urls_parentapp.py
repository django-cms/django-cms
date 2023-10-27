from django.urls import path

from cms.test_utils.project.sampleapp import views

urlpatterns = [
    path('<path:path>', views.parentapp_view, name='parentapp_view'),
]
