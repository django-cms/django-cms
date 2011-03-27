from cms.toolbar.base import Toolbar
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse


def toolbar(toolbar_class, *tbc_args, **tbc_kwargs):
    """
    Decorator for views.
    """
    if not issubclass(toolbar_class, Toolbar):
        raise ImproperlyConfigured("The cms.toolbar.toolbar decorator must be "
                                   "used with a cms.toolbar.base.Toolbar "
                                   "subclass  as first argument.")
    def _decorator(view):
        def _wrapped(request, *args, **kwargs):
            request.toolbar = toolbar_class(*tbc_args, **tbc_kwargs)
            response = request.toolbar.request_hook(request)
            if isinstance(response, HttpResponse):
                return response
            return view(request, *args, **kwargs)
        _wrapped.__name__ = view.__name__
        return _wrapped
    return _decorator