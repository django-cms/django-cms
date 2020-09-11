from django.urls import re_path

from ..placeholderapp import views

app_name = 'example_app'

urlpatterns = [
    re_path(r'^example/$', views.example_view, name="example"),
]
