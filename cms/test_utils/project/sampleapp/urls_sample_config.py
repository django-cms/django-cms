from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.sample_view, {'message': 'sample root page',}, name='sample-config-root'),
]
