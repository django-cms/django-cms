# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from . import models
from . import views


class PandadocDocumentSenderCMSPlugin(CMSPluginBase):
    render_template = 'project/pandadoc_document_sender.html'
    name = _('Pandadoc Document Sender')
    model = models.PandadocDocumentSenderPlugin
    cache = False

    def get_plugin_urls(self):
        return [
            url(r'^send-document/$', views.send_pandadoc_document, name='pandadoc-send-document'),
        ]

    def render(self, context, instance, placeholder):
        context = super(PandadocDocumentSenderCMSPlugin, self).render(context, instance, placeholder)
        context['recaptcha_sitekey'] = settings.RECAPTCHA_SITE_KEY
        return context

plugin_pool.register_plugin(PandadocDocumentSenderCMSPlugin)
