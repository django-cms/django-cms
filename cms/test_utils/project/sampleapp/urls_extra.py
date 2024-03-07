from django.urls import path

from . import views

urlpatterns = [
    path('extra_2/', views.extra_view, {'message': 'test included urlconf'}, name='extra_second'),
]
