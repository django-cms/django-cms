import importlib

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext as _

from cms.utils.conf import get_cms_setting


def get_request_ip_resolver():
    """
    This is the recommended method for obtaining the specified
    CMS_REQUEST_IP_RESOLVER as it also does some basic import validation.

    Returns the resolver or raises an ImproperlyConfigured exception.
    """
    module, attribute = get_cms_setting('REQUEST_IP_RESOLVER').rsplit('.', 1)
    try:
        ip_resolver_module = importlib.import_module(module)
        ip_resolver = getattr(ip_resolver_module, attribute)
    except ImportError as err:
        raise ImproperlyConfigured(
            _('Unable to find the specified CMS_REQUEST_IP_RESOLVER module: '
              '"{0}".').format(module)) from err
    except AttributeError as err:
        raise ImproperlyConfigured(
            _('Unable to find the specified CMS_REQUEST_IP_RESOLVER function: '
              '"{0}" in module "{1}".').format(attribute, module)) from err
    return ip_resolver


def default_request_ip_resolver(request):
    """
    This is a hybrid request IP resolver that attempts should address most
    cases. Order is important here. A 'REAL_IP' header supersedes an
    'X_FORWARDED_FOR' header which supersedes a 'REMOTE_ADDR' header.
    """
    return (
        real_ip(request) or x_forwarded_ip(request) or remote_addr_ip(request)
    )


def real_ip(request):
    """
    Returns the IP Address contained in the HTTP_X_REAL_IP headers, if
    present. Otherwise, `None`.

    Should handle Nginx and some other WSGI servers.
    """
    return request.headers.get('X-Real-Ip')


def remote_addr_ip(request):
    """
    Returns the IP Address contained in the 'REMOTE_ADDR' header, if
    present. Otherwise, `None`.

    Should be suitable for local-development servers and some HTTP servers.
    """
    return request.META.get('REMOTE_ADDR')


def x_forwarded_ip(request):
    """
    Returns the IP Address contained in the 'HTTP_X_FORWARDED_FOR' header, if
    present. Otherwise, `None`.

    Should handle properly configured proxy servers.
    """
    ip_address_list = request.headers.get('X-Forwarded-For')
    if ip_address_list:
        ip_address_list = ip_address_list.split(',')
        return ip_address_list[0]
