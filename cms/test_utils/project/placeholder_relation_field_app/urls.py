from django.conf.urls import url

from .views import detail


urlpatterns = [
    url(r'^detail/([0-9]+)/$', detail, name='detail_view'),
]
