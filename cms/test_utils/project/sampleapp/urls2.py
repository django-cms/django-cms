from django.urls import path

from . import views

urlpatterns = [
    path('', views.sample_view, {'message': 'sample apphook2 root page', }, name='sample2-root'),
]
