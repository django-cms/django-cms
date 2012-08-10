# -*- coding: utf-8 -*-
from django.db import models
import reversion
from reversion.revisions import RegistrationError, VersionAdapter

def register_draft_only(model_class, fields, follow, format):
    """
    version of the reversion register function that only registers drafts and
    ignores public models
    """
    revision_manager = reversion.revision
    if revision_manager.is_registered(model_class):
        raise RegistrationError(
            "%r has already been registered with Reversion." % model_class)

    # Ensure the parent model of proxy models is registered.
    if (model_class._meta.proxy and
        not revision_manager.is_registered(model_class._meta.parents.keys()[0])):
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
    revision_manager._registered_models[model_class] = registration_info
    # Do not connect to the post save signal of the model.
