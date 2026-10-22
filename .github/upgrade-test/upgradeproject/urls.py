from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path

urlpatterns = i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("cms.urls")),
)
