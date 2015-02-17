from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^detail/(?P<pk>[0-9]+)/$', views.detail_view_multi, name="detail_multi"),
    url(r'^$', views.list_view_multi, name="list_multi"),
]
