"""Django permission helpers that belong to no container.

``get_model_permission_codename`` turns a model and an action into the dotted
codename ``user.has_perm`` expects. Nothing about it is CMS-specific, and core,
pages and permissions all need it, so it lives here.
"""

from django.contrib.auth import get_permission_codename

__all__ = ["get_model_permission_codename"]


def get_model_permission_codename(model, action):
    opts = model._meta
    return opts.app_label + '.' + get_permission_codename(action, opts)
