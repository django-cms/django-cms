# -*- coding: utf-8 -*-

from reversion.revisions import RegistrationError

try:
    # django-reversion >= 2
    from reversion.revisions import _VersionOptions as VersionAdapter
except ImportError:
    # django-reversion < 2
    from reversion.revisions import VersionAdapter

try:
    # 1.10 >= django-reversion < 2
    from reversion import revisions as reversion
    revision_manager = reversion.default_revision_manager
except ImportError:
    # django-reversion < 1.10
    import reversion
    revision_manager = reversion.revision
except AttributeError:
    # django-reversion >= 2
    from reversion import revisions

    class revision_manager(object):

        _registered_models = revisions._registered_models

        @staticmethod
        def _registration_key_for_model(*args, **kwargs):
            return revisions._get_registration_key(*args, **kwargs)

        @staticmethod
        def is_registered(*args, **kwargs):
            return revisions.is_registered(*args, **kwargs)


def register_draft_only(model_class, fields, follow, format):
    """
    version of the reversion register function that only registers drafts and
    ignores public models
    """
    # FIXME: Remove this when integrating djangocms-reversion
    if revision_manager.is_registered(model_class):
        raise RegistrationError(
            "%r has already been registered with Reversion." % model_class)

    # Ensure the parent model of proxy models is registered.
    if (model_class._meta.proxy and
        not revision_manager.is_registered(list(model_class._meta.parents.keys())[0])): # turn KeysView into list
        raise RegistrationError(
            '%r is a proxy model, and its parent has not been registered with'
            'Reversion.' % model_class)

    # Calculate serializable model fields.
    opts = model_class._meta
    local_fields = opts.local_fields + opts.local_many_to_many
    if fields is None:
        fields = [field.name for field in local_fields]
    fields = tuple(fields)

    # Register the generated registration information.
    follow = tuple(follow)

    try:
        registration_info = VersionAdapter(
            fields=fields,
            follow=follow,
            format=format,
            for_concrete_model=True,
            ignore_duplicates=False,
        )
    except TypeError:
        registration_info = VersionAdapter(model_class)
        registration_info.fields = fields
        registration_info.follow = follow
        registration_info.format = format
    if hasattr(revision_manager, '_registration_key_for_model'):
        model_key = revision_manager._registration_key_for_model(model_class)
    else:
        model_key = model_class
    revision_manager._registered_models[model_key] = registration_info
    # Do not connect to the post save signal of the model.
