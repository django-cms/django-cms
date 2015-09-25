# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import patterns, url

from .views import WizardCreateView


urlpatterns = patterns('',  # NOQA
    url(r'^create/$',
        WizardCreateView.as_view(), name='wizard_create'),
)
