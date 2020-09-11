from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'extra_2/$', views.extra_view, {'message': 'test included urlconf'}, name='extra_second'),
]
