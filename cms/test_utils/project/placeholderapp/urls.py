from django.urls import path
from django.urls import re_path

from . import views
from .views import ClassDetail

urlpatterns = [
    path('detail/<int:pk>/', views.detail_view, name="example_detail"),
    re_path(r'^detail_char/(?P<pk>[a-z]+)/$', views.detail_view_char, name="example_detail_char"),
    path('detail/class/<int:pk>/', ClassDetail.as_view(), name="example_class_detail"),
    path('', views.list_view, name="example_list"),
]
