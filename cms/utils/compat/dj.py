try:
    from django.utils.encoding import force_unicode
except ImportError:
    force_unicode = lambda s: str(s)