# -*- coding: utf-8 -*-
from functools import partial

from aldryn_client import forms


class Form(forms.BaseForm):

    def to_settings(self, data, settings):
        from django.core.urlresolvers import reverse_lazy

        from aldryn_addons.utils import djsenv

        env = partial(djsenv, settings=settings)

        cloud_sync_key = env('CMSCLOUD_SYNC_KEY')
        credential_url = env('LIVERELOAD_CREDENTIAL_URL')

        if 'aldryn_snake.template_api.template_processor' not in settings['TEMPLATE_CONTEXT_PROCESSORS']:
            settings['TEMPLATE_CONTEXT_PROCESSORS'].append('aldryn_snake.template_api.template_processor')

        if cloud_sync_key and credential_url:
            settings['LIVERELOAD_CREDENTIAL_URL'] = credential_url
            # By selectively adding the urls, we avoid having to do
            # all sorts of checks in the views, instead the views
            # have no logic as to what settings are required or not.
            settings['ADDON_URLS'].append('aldryn_devsync.urls')
            settings['INSTALLED_APPS'].append('aldryn_devsync')

        if 'ALDRYN_SSO_LOGIN_WHITE_LIST' in settings:
            # stage sso enabled
            # add internal endpoints that do not require authentication
            settings['ALDRYN_SSO_LOGIN_WHITE_LIST'].extend([
                reverse_lazy('devsync-add-file'),
                reverse_lazy('devsync-delete-file'),
                reverse_lazy('devsync-run-command'),
                reverse_lazy('livereload-iframe-content'),
                reverse_lazy('toggle-livereload'), #TODO: is ok for this to be white listed?
                reverse_lazy('devsync-trigger-sync'),
            ])

        settings['CMSCLOUD_SYNC_KEY'] = cloud_sync_key
        settings['LAST_BOILERPLATE_COMMIT'] = env('LAST_BOILERPLATE_COMMIT')
        settings['SYNC_CHANGED_FILES_URL'] = env('SYNC_CHANGED_FILES_URL')
        settings['SYNC_CHANGED_FILES_SIGNATURE_MAX_AGE'] = 60  # seconds
        return settings
