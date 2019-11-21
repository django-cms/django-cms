# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import View

import requests

from . import models


class SendPandadocDocument(View):
    base_url = 'https://api.pandadoc.com/'
    recipients = [
        {
            # our party
            'email': 'legal@divio.com',
            'first_name': 'Jon',
            'last_name': 'Levin',
            'role': 'Divio',
        },
        {
            # for notification
            'email': 'joel.burch@divio.com',
            'first_name': 'Joel',
            'last_name': 'Burch',
        },
    ]

    def url(self, endpoint):
        return self.base_url + endpoint

    def return_response(self, request, success, exc=None):
        if exc:
            message = (
                str(exc) if request.user.is_staff else
                'An unknown error has occurred.'
            )
        else:
            message = None

        if request.is_ajax():
            response = {'success': success}
            if message:
                response['message'] = message
            return JsonResponse(response)
        else:
            if not success:
                messages.warning(
                    request,
                    'There was an unexpected error. '
                    'Please contact support.'
                )
            return HttpResponseRedirect('/')

    def post(self, request, *args, **kwargs):
        plugin = get_object_or_404(
            models.PandadocDocumentSenderPlugin,
            id=request.POST.get('plugin_id'),
        )

        # 1) check captcha with Google
        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': request.POST.get('g-recaptcha-response'),
                }
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return self.return_response(request, False, exc)

        # 2) refresh the access token if needed
        if plugin.authentication.is_expired:
            success = plugin.refresh_authorization()
            if not success:
                return self.return_response(request, False)
            plugin = plugin.refresh_from_db()

        # 3) Create document on PandaDoc
        headers = plugin.authentication.headers

        recipient = dict(
            email=request.POST.get('recipient_email'),
            first_name=request.POST.get('recipient_first_name'),
            last_name=request.POST.get('recipient_last_name'),
        )

        if plugin.role:
            recipient['role'] = plugin.role

        request_data = dict(
            name=plugin.document_name,
            template_uuid=plugin.template_uuid,
            recipients=self.recipients + [recipient],
        )

        try:
            response = requests.post(
                self.url('public/v1/documents'),
                data=json.dumps(request_data), headers=headers,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return self.return_response(request, False, exc)

        document_id = response.json()['uuid']

        # 4) Send documents to involved people
        request_data = dict(message=plugin.message_content)

        try:
            response = requests.post(
                self.url('public/v1/documents/{}/send'.format(document_id)),
                data=json.dumps(request_data), headers=headers,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return self.return_response(request, False, exc)

        return self.return_response(request, True)


send_pandadoc_document = SendPandadocDocument.as_view()
