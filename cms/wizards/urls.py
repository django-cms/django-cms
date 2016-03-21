# -*- coding: utf-8 -*-

from django.conf.urls import url

from .views import WizardCreateView


urlpatterns = [
    url(r"^create/$",
        WizardCreateView.as_view(), name="cms_wizard_create"),
]
