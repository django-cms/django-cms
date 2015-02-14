from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.sample_view, {'message': 'sample apphook2 root page', }, name='sample2-root'),
]
