# -*- coding: utf-8 -*-
from cms.utils.conf import get_cms_setting
import warnings


def cms_settings(request):
    """
    Adds media-related context variables to the context.
    """
    try:
        template = request.current_page.get_template()
    except AttributeError:
        template = ''
    return {
        'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
        'PAGE_TEMPLATE': template,
    }


def media(request):
    warnings.warn('cms.context_processors.media has been deprecated in favor of'
                  'cms.context_processors.cms_settings. Please update your'
                  'configuration', DeprecationWarning)
    return cms_settings(request)