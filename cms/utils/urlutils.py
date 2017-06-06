# -*- coding: utf-8 -*-
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.encoding import force_text
from django.utils.http import urlencode
from django.utils.six.moves.urllib.parse import urlparse

import cms

from cms.utils.conf import get_cms_setting

# checks validity of absolute / relative url
any_path_re = re.compile('^/?[a-zA-Z0-9_.-]+(/[a-zA-Z0-9_.-]+)*/?$')

# checks validity of relative url
# matches the following:
# /test
# /test/
# ./test/
# ../test/
relative_url_regex = re.compile(r'^[^/<>]+/[^/<>].*$|^/[^/<>]*.*$', re.IGNORECASE)


def levelize_path(path):
    """Splits given path to list of paths removing latest level in each step.

    >>> path = '/application/item/new'
    >>> levelize_path(path)
    ['/application/item/new', '/application/item', '/application']
    """
    parts = tuple(filter(None, path.split('/')))
    return ['/' + '/'.join(parts[:n]) for n in range(len(parts), 0, -1)]


def urljoin(*segments):
    """Joins url segments together and appends trailing slash if required.

    >>> urljoin('a', 'b', 'c')
    u'a/b/c/'

    >>> urljoin('a', '//b//', 'c')
    u'a/b/c/'

    >>> urljoin('/a', '/b/', '/c/')
    u'/a/b/c/'

    >>> urljoin('/a', '')
    u'/a/'
    """
    url  = '/' if segments[0].startswith('/') else ''
    url += '/'.join(filter(None, (force_text(s).strip('/') for s in segments)))
    return url + '/' if settings.APPEND_SLASH else url


def is_media_request(request):
    """
    Check if a request is a media request.
    """
    parsed_media_url = urlparse(settings.MEDIA_URL)
    if request.path_info.startswith(parsed_media_url.path):
        if parsed_media_url.netloc:
            if request.get_host() == parsed_media_url.netloc:
                return True
        else:
            return True
    return False


def static_with_version(path):
    """
    Changes provided path from `path/to/filename.ext` to `path/to/$CMS_VERSION/filename.ext`
    """
    path_re = re.compile('(.*)/([^/]*$)')

    return re.sub(path_re, r'\1/%s/\2' % (cms.__version__), path)


def add_url_parameters(url, *args, **params):
    """
    adds parameters to an url -> url?p1=v1&p2=v2...
    :param url: url without any parameters
    :param args: one or more dictionaries containing url parameters
    :param params: url parameters as keyword arguments
    :return: url with parameters if any
    """
    for arg in args:
        params.update(arg)
    if params:
        return '%s?%s' % (url, urlencode(params))
    return url


def admin_reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None,
                  current_app=None):
    admin_namespace = get_cms_setting('ADMIN_NAMESPACE')
    if ':' in viewname:
        raise ValueError(
            "viewname in admin_reverse may not already have a namespace "
            "defined: {0!r}".format(viewname)
        )
    viewname = "{0}:{1}".format(admin_namespace, viewname)
    return reverse(
        viewname,
        urlconf=urlconf,
        args=args,
        kwargs=kwargs,
        current_app=current_app
    )
