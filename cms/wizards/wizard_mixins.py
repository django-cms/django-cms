# -*- coding: utf-8 -*-

import urllib
import urlparse


# TODO: This appears to be project-specific code that makes everything enter
# edit-mode.

class CMSWizardMixin(object):
    def get_success_url(self, obj, *args, **kwargs):
        absolute_url = super(CMSWizardMixin, self).get_success_url(
            obj, *args, **kwargs)
        url_parts = list(urlparse.urlparse(absolute_url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        query.update({'edit': '1'})
        url_parts[4] = urllib.urlencode(query)
        return urlparse.urlunparse(url_parts)
