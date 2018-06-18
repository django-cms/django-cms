# -*- coding: utf-8 -*-

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

# TODO:
#  - Add page Logging should be implemented in: AddPageForm so the wizard and admin form both fire the log as the wizard does not currently.

"""
Logs are all collected here to keep the messages and contents consistent across all operations.
May seem repetitive but allows each log to be unique for different circumstances.
Method names make the log being created clear and concise

Issues with current solution:
    - A log entry isn't created when a page is created using the new page wizard. Again showing a flaw with testing via the API and not the actual fn's!!
    - Difficult to find the log page creation in the current solution!! The existing implementation,uses the LogEntry model directly, others use the ModelAdmin Implementation. There should be one way where possible!!

Design Considerations:
    - Allow plugins to integrate with the CMS logger??
    - A log helper method "create_log" that uses LogEntry and allows the removal of LogEntry at a later date.
    - A page move event is recorded as CHANGE with no message. A "Moved." message has been manually added
    - Django admin keeps all logs in one area rather than spreading them out and potentially having them set inconsistently and scattered in multiple files.
"""


"""
Log helper
"""


def create_log(user_id, content_type_id, object_id, object_repr, action_flag, change_message):
    """
    Helper method
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