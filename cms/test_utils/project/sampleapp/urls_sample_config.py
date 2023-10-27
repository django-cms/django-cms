from django.urls import path

from . import views

urlpatterns = [
    path('', views.sample_view, {'message': 'sample root page', }, name='sample-config-root'),
]
