# -*- coding: utf-8 -*-
try:
    from reversion.revisions import RegistrationError, VersionAdapter, default_revision_manager
except ImportError as e:
    from reversion import default_revision_manager
    from reversion.revisions import RegistrationError, VersionAdapter


def register_draft_only(model_class, fields, follow, format):
    """
    version of the reversion register function that only registers drafts and
    ignores public models
    """
    if default_revision_manager.is_registered(model_class):
        raise RegistrationError(
            "%r has already been registered with Reversion." % model_class)

    # Ensure the parent model of proxy models is registered.
    if (model_class._meta.proxy and
        not default_revision_manager.is_registered(list(model_class._meta.parents.keys())[0])): # turn KeysView into list
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
    registration_info = VersionAdapter(model_class)
    registration_info.fields = fields
    registration_info.follow = follow
    registration_info.format = format
    if hasattr(default_revision_manager, '_registration_key_for_model'):
        model_key = default_revision_manager._registration_key_for_model(model_class)
    else:
        model_key = model_class
    default_revision_manager._registered_models[model_key] = registration_info
    # Do not connect to the post save signal of the model.
