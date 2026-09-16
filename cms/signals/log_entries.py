import json

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.models import Page, PageType

_page_operations_map = {
    operations.MOVE_PAGE: {
        'message': _("Moved"),
        'flag': CHANGE,
    },
    operations.CHANGE_PAGE: {
        'message': _("Changed"),
        'flag': CHANGE,
    },
    operations.DELETE_PAGE: {
        'message': _("Deleted"),
        'flag': DELETION,
    },
    operations.ADD_PAGE_TRANSLATION: {
        'message': _("Added Page Translation"),
        'flag': ADDITION,
    },
    operations.CHANGE_PAGE_TRANSLATION: {
        'message': _("Changed Page Translation"),
        'flag': CHANGE,
    },
    operations.DELETE_PAGE_TRANSLATION: {
        'message': _("Deleted Page Translation"),
        'flag': CHANGE,
    },
}

_placeholder_operations_map = {
    operations.ADD_PLUGIN: {
        'message': _("Added Plugin"),
        'flag': CHANGE,
        'placeholder_kwarg': 'placeholder'
    },
    operations.CHANGE_PLUGIN: {
        'message': _("Changed Plugin"),
        'flag': CHANGE,
        'placeholder_kwarg': 'placeholder'
    },
    operations.MOVE_PLUGIN: {
        'message': _("Moved Plugin"),
        'flag': CHANGE,
        'placeholder_kwarg': 'target_placeholder'
    },
    operations.DELETE_PLUGIN: {
        'message': _("Deleted Plugin"),
        'flag': CHANGE,
        'placeholder_kwarg': 'placeholder'
    },
    operations.CUT_PLUGIN: {
        'message': _("Cut Plugin"),
        'flag': CHANGE,
        'placeholder_kwarg': 'source_placeholder'
    },
    operations.PASTE_PLUGIN: {
        'message': _("Paste Plugin"),
        'flag': CHANGE,
        'placeholder_kwarg': 'target_placeholder'
    },
    operations.PASTE_PLACEHOLDER: {
        'message': _("Paste to Placeholder"),
        'flag': CHANGE,
        'placeholder_kwarg': 'target_placeholder'
    },
    operations.ADD_PLUGINS_FROM_PLACEHOLDER: {
        'message': _("Added plugins to placeholder from clipboard"),
        'flag': CHANGE,
        'placeholder_kwarg': 'target_placeholder'
    },
    operations.CLEAR_PLACEHOLDER: {
        'message': _("Cleared Placeholder"),
        'flag': CHANGE,
        'placeholder_kwarg': 'placeholder'
    },
}


def create_log_entry(user_id, content_type_id, object_id, object_repr, action_flag, change_message):
    if isinstance(change_message, list):
        change_message = json.dumps(change_message)

    LogEntry.objects.create(
            user_id=user_id,
            content_type_id=content_type_id,
            object_id=str(object_id),
            object_repr=object_repr[:200],
            action_flag=action_flag,
            change_message=change_message,
        )


def _acting_user(kwargs):
    """The user behind an operation.

    Operations reach here from the admin, where there is a request, and from the
    service layer, where there may not be -- so the explicit ``user`` kwarg wins
    and the request is only a fallback for receivers of older signals.
    """
    user = kwargs.get("user")
    if user is not None:
        return user
    request = kwargs.get("request")
    return getattr(request, "user", None)


def _is_valid_page_instance(page):
    """
    Check if the supplied object is a valid Page / PageType object
    """
    return isinstance(page, (Page, PageType))


def log_page_operations(sender, **kwargs):
    """
    Create a log for the correct page operation type
    """
    user = _acting_user(kwargs)
    operation_type = kwargs.get('operation')
    obj = kwargs.get('obj')

    # Check that we have instructions for the operation
    # and an instance of Page to link to in the log
    if user is not None and operation_type in _page_operations_map and _is_valid_page_instance(obj):
        operation_handler = _page_operations_map[operation_type]
        content_type_id = ContentType.objects.get_for_model(obj).pk
        create_log_entry(
            user_id=user.pk,
            content_type_id=content_type_id,
            object_id=obj.pk,
            object_repr=str(obj),
            action_flag=operation_handler['flag'],
            change_message=operation_handler['message'],
        )


def log_placeholder_operations(sender, **kwargs):
    """
    Create a log for the correct placeholder operation type
    """
    user = _acting_user(kwargs)
    operation_type = kwargs.get('operation')

    # Check that we have instructions for the operation
    if user is not None and operation_type in _placeholder_operations_map:
        operation_handler = _placeholder_operations_map[operation_type]
        placeholder = kwargs.get(operation_handler['placeholder_kwarg'])
        page = placeholder.page

        # Check that we have an instance of Page to link to in the log
        if _is_valid_page_instance(page):
            content_type_id = ContentType.objects.get_for_model(page).pk
            create_log_entry(
                user_id=user.pk,
                content_type_id=content_type_id,
                object_id=page.pk,
                object_repr=str(page),
                action_flag=operation_handler['flag'],
                change_message=operation_handler['message'],
            )
