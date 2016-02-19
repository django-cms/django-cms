# -*- coding: utf-8 -*-

# This large try / except is to account for reversion 1.10 (top) / 1.8 (bottom) support
# This will go away in CMS 3.3 when only reversion 1.10 will be supported
try:
    from reversion import revisions as reversion
    from reversion.admin import VersionAdmin as ModelAdmin, RollBackRevisionView  # NOQA  # nopyflakes
    from reversion.models import Revision, Version  # NOQA  # nopyflakes
    from reversion.revisions import create_revision, RegistrationError, VersionAdapter  # NOQA  # nopyflakes
    from reversion.signals import post_revision_commit  # NOQA  # nopyflakes

    revision_manager = reversion.default_revision_manager
    revision_context = reversion.revision_context_manager
except ImportError:
    import reversion
    from reversion import create_revision  # NOQA  # nopyflakes
    from reversion.admin import VersionAdmin as ModelAdmin  # NOQA  # nopyflakes
    from reversion.models import Revision, Version, post_revision_commit  # NOQA  # nopyflakes
    from reversion.revisions import RegistrationError, VersionAdapter  # NOQA  # nopyflakes

    revision_manager = reversion.revision
    revision_context = reversion.revision_context_manager

    class RollBackRevisionView(Exception):
        pass


def register_draft_only(model_class, fields, follow, format):
    """
    version of the reversion register function that only registers drafts and
    ignores public models
    """
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
