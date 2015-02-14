from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'extra_2/$', views.extra_view, {'message': 'test included urlconf'}, name='extra_second'),
]
