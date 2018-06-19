# -*- coding: utf-8 -*-

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


"""
Log helper
"""


def create_log(user_id, content_type_id, object_id, object_repr, action_flag, change_message):
    """
    Although this function is repetitive it allows external plugins to access the same logging mechanisms as the cms
    It also removes the dependency of the admin LogEntry in any other Django CMS code
    """
    return LogEntry.objects.log_action(
        user_id=user_id,
        content_type_id=content_type_id,
        object_id=object_id,
        object_repr=object_repr,
        action_flag=action_flag,
        change_message=change_message,
    )

"""
Page logs
"""


def log_page_form_addition(user, page_object, message=""):
    """
    Log that a page object has been successfully created.
    """

    create_log(
        user_id=user.pk,
        content_type_id=ContentType.objects.get_for_model(page_object).pk,
        object_id=page_object.pk,
        object_repr=str(page_object),
        action_flag=ADDITION,
        change_message=message,
    )


def log_page_addition(request, page_object, message=""):
    """
    Log that a page object has been successfully created.
    """

    create_log(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(page_object).pk,
        object_id=page_object.pk,
        object_repr=str(page_object),
        action_flag=ADDITION,
        change_message=message,
    )


def log_page_change(request, page_object, change_list=""):
    """
    Log that a page object has been successfully changed.
    """

    create_log(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(page_object).pk,
        object_id=page_object.pk,
        object_repr=str(page_object),
        action_flag=CHANGE,
        change_message=change_list,
    )


def log_page_move(request, page_object, message=""):
    """
    Log that a page object has been successfully moved.
    """

    # FIXME: REMOVEME: @Paulo this is set due to the fact that a page move is a CHANGE but no fields are changed so Django sets it as an empty message by default
    if message == "":
        message = _("Moved.")

    create_log(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(page_object).pk,
        object_id=page_object.pk,
        object_repr=str(page_object),
        action_flag=CHANGE,
        change_message=message,
    )


def log_page_delete(request, page_object, object_repr, message=""):
    """
    Log that a page object has been successfully deleted.
    """

    create_log(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(page_object).pk,
        object_id=page_object.pk,
        object_repr=object_repr,
        action_flag=DELETION,
        change_message=message,
    )


# TODO:
"""
Title logs
"""

"""
Placeholder logs
"""

"""
Plugin logs
"""