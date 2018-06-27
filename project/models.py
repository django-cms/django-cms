# -*- coding: utf-8 -*-
from datetime import timedelta

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from cms.models.pluginmodel import CMSPlugin

import requests


class PandadocAuthentication(models.Model):
    name = models.CharField(
        _('Authentication name'),
        max_length=255,
        help_text=_(
            'Can be anything useful to help identify this authentication '
            'object amongst others.'
        )
    )
    client_id = models.CharField(
        _('Client ID'),
        max_length=255,
    )
    client_secret = models.CharField(
        _('Client secret'),
        max_length=255,
    )
    redirect_uri = models.CharField(
        _('Redirect URI'),
        max_length=255,
    )
    scope = models.CharField(
        _('Scope'),
        max_length=255,
        default='read+write',
    )
    access_token = models.CharField(
        _('Access token'),
        max_length=255,
        blank=True,
        default='',
    )
    refresh_token = models.CharField(
        _('Refresh token'),
        max_length=255,
        blank=True,
        default='',
    )
    token_expiration = models.DateTimeField(
        _('Token expiration'),
        blank=True,
        null=True,
    )

    @property
    def is_expired(self):
        if self.token_expiration:
            return self.token_expiration < timezone.now()

    @property
    def headers(self):
        return {
            'Authorization': 'Bearer {}'.format(self.access_token),
            'Content-Type': 'application/json;charset=UTF-8',
        }

    def get_or_update_token(self, grant_type, authorization_code=None):
        data = dict(
            grant_type=grant_type,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=self.scope,
            redirect_uri=self.redirect_uri,
        )

        if grant_type == 'authorization_code':
            data['code'] = authorization_code

        elif grant_type == 'refresh_token':
            data['refresh_token'] = self.refresh_token
        else:
            raise NotImplementedError

        try:
            response = requests.post(
                'https://app.pandadoc.com/oauth2/access_token',
                data=data,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return False, exc

        response = response.json()
        self.access_token = response['access_token']
        self.refresh_token = response['refresh_token']
        self.token_expiration = timezone.now() + timedelta(seconds=response['expires_in'])
        self.save(update_fields=(
            'access_token',
            'refresh_token',
            'token_expiration',
        ))
        return True, None

    def apply_authorization(self, authorization_code):
        """Exchange the OAuth authorization with an access and refresh token"""
        return self.get_or_update_token(
            grant_type='authorization_code',
            authorization_code=authorization_code,
        )

    def refresh_authorization(self):
        return self.get_or_update_token(
            grant_type='refresh_token',
        )

    def __str__(self):
        return '{}{} ({})'.format(
            '[expired] ' if self.is_expired else '',
            self.name,
            self.client_id,
        )


class PandadocDocumentSenderPlugin(CMSPlugin):
    document_name = models.CharField(
        max_length=255, verbose_name=_('Pandadoc Document Name'),
    )
    template_uuid = models.CharField(
        max_length=255, verbose_name=_('Pandadoc Template UUID'),
        help_text=_(
            'You can copy it from a template url '
            '(https://app.pandadoc.com/a/#/templates/{UUID}/content).'
        )
    )
    message_content = models.TextField(
        verbose_name=_('Content for signing email')
    )
    role = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name=_('Role for invited person'),
        help_text=_(
            'If passed, a person will be assigned all fields which match his '
            'or her corresponding role. If not passed, a person will receive '
            'a read-only link to view the document.'
        )
    )
    authentication = models.ForeignKey(
        PandadocAuthentication,
        verbose_name=_('Authentication'),
        blank=True,
        null=True,
    )

    def __unicode__(self):
        return u'{} ({})'.format(
            self.document_name,
            self.template_uuid,
        )
