# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

from .views import WizardCreateView


urlpatterns = patterns('',  # NOQA
    url(r"^create/$",
        WizardCreateView.as_view(), name="cms_wizard_create"),
)
