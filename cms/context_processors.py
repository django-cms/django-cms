# -*- coding: utf-8 -*-
from cms.utils.conf import get_cms_setting
from cms.utils import get_template_from_request


def cms_settings(request):
    """
    Adds cms-related variables to the context.
    """

    return {
        'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
        'CMS_TEMPLATE': lambda: get_template_from_request(request),
    }
