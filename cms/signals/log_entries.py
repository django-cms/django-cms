from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from cms import operations


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
    """
    Create a log entry
    """
    return LogEntry.objects.log_action(
        user_id=user_id,
        content_type_id=content_type_id,
        object_id=object_id,
        object_repr=object_repr,
        action_flag=action_flag,
        change_message=change_message,
    )


def log_page_operations(sender, **kwargs):
    """
    Create a log for the correct page operation type
    """

    request = kwargs.pop('request')
    operation_type = kwargs.pop('operation')
    obj = kwargs.pop('obj')

    if operation_type in _page_operations_map:

        operation_handler = _page_operations_map[operation_type]
        user_id = request.user.pk
        content_type_id = ContentType.objects.get_for_model(obj).pk
        object_id = obj.pk
        object_repr = str(obj)

        create_log_entry(user_id, content_type_id, object_id, object_repr, operation_handler['flag'], operation_handler['message'])


def log_placeholder_operations(sender, **kwargs):
    """
    Create a log for the correct placeholder operation type
    """

    request = kwargs.pop('request')
    operation_type = kwargs.pop('operation')

    if operation_type in _placeholder_operations_map:

        operation_handler = _placeholder_operations_map[operation_type]
        user_id = request.user.pk
        placeholder = kwargs.pop(operation_handler['placeholder_kwarg'])
        page = placeholder.page
        content_type_id = ContentType.objects.get_for_model(page).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, operation_handler['flag'], operation_handler['message'])
