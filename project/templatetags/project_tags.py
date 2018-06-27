from __future__ import absolute_import

import hashlib
import hmac

from django import template


register = template.Library()


@register.filter()
def hmac_str(userid, key):
    """Return the encrypted key"""
    key = bytes(key, 'latin-1')
    data = bytes('aldryn-cloud-id_' + str(userid), 'latin-1')
    return hmac.new(
        key,
        data,
        digestmod=hashlib.sha256
    ).hexdigest()
