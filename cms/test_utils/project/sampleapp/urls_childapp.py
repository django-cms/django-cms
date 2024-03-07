from django.urls import path

from cms.test_utils.project.sampleapp import views

urlpatterns = [
    path('<path:path>', views.childapp_view, name='childapp_view'),
]
