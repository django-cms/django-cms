# -*- coding: utf-8 -*-
from cms.utils.conf import get_cms_setting
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from cms.utils.compat.urls import urlparse
from cms.utils.compat.dj import force_unicode
import re

# checks validity of absolute / relative url
any_path_re = re.compile('^/?[a-zA-Z0-9_.-]+(/[a-zA-Z0-9_.-]+)*/?$') 


def levelize_path(path):
    """Splits given path to list of paths removing latest level in each step.
    
    >>> path = '/application/item/new'
    >>> levelize_path(path)
    ['/application/item/new', '/application/item', '/application']
    """
    parts = path.rstrip("/").split("/")
    paths = []
    for i in range(len(parts), 0, -1):
        sub_path = ('/').join(parts[:i])
        if sub_path:
            paths.append(sub_path)
    return paths


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
    cleaned_segments = map(lambda segment: force_unicode(segment).strip("/"), segments)
    nonempty_segments = filter(lambda segment: segment > "", cleaned_segments)
    url = ("/").join(nonempty_segments)
    
    if segments[0].startswith("/") and not url.startswith("/"):
        url = "/" + url
    
    if settings.APPEND_SLASH and not url.endswith("/"):
        url += "/"
    return url


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
        prefix=prefix,
        current_app=current_app
    )
