from django.core.exceptions import ImproperlyConfigured


def patch_hook(method):
    """Decorator to mark methods or functions that might be patched by a supporting package like
    djangocms-versioning or djangocms-moderation.

    .. warning::

        Do not rename or move this method since other packages depend on

    """
    if isinstance(method, property):
        method.fget._is_cms_patch_hook = True
    else:
        method._is_cms_patch_hook = True
    return method


def patch_cms(obj, method, patch):
    """Patches a cms method which has been marked with the @patch_hook decorator. It's parameters are those
    of setattr."""
    if hasattr(obj, method):
        if isinstance(getattr(obj, method), property):
            # For properties the getter is marked
            if getattr(getattr(obj, method).fget, "_is_cms_patch_hook", False):
                patch.fget._is_cms_patch_hook = True
                setattr(obj, method, patch)
                return

        if getattr(getattr(obj, method), "_is_cms_patch_hook", False):
            patch._is_cms_patch_hook = True  # The patch also can be patched
            setattr(obj, method, patch)
            return

    import inspect

    caller = inspect.currentframe().f_back
    (filename, line_number, function_name, lines, index) = inspect.getframeinfo(caller)
    module_name = f"({obj.__module__}) " if hasattr(obj, "__module__") else ""
    raise ImproperlyConfigured(f"File {filename} in line {line_number} tried to patch {method} of {obj.__name__} "
                               f"{module_name}but there is no method marked as @patch_hook.")
