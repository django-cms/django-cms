# -*- coding: utf-8 -*-
from django.conf import settings
from urlparse import urlparse
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
    cleaned_segments = map(lambda segment: unicode(segment).strip("/"), segments)
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
    if request.path.startswith(parsed_media_url.path):
        if parsed_media_url.netloc:
            if request.get_host() == parsed_media_url.netloc:
                return True
        else:
            return True
    return False 