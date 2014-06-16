# -*- coding: utf-8 -*-
try:
    from urllib import urlencode
    from urlparse import urlparse, urljoin
    from urllib import unquote
except ImportError:
    from urllib.parse import urlencode  # nopyflakes
    from urllib.parse import urlparse  # nopyflakes
    from urllib.parse import unquote  # nopyflakes
    from urllib.parse import urljoin  # nopyflakes
