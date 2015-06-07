from django.conf.urls import url

from cms.test_utils.project.sampleapp import views

urlpatterns = [
    url(r'^(?P<path>.+)$', views.parentapp_view, name='parentapp_view'),
]
