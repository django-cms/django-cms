from django.urls import path

from ..placeholderapp import views

app_name = 'example_app'

urlpatterns = [
    path('example/', views.example_view, name="example"),
]
