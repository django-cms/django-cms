from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from cms import operations

# listen for the post_obj_operation signals for pages and post_placeholder_operation signal for placeholders and plugins.
# log_entries.py in cms/signals/ and there add all the necessary handlers.
# create a page specific handler which receives the operation type and then map operation types to action flags.


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


_page_operations_map = {
    operations.MOVE_PAGE: {
        'message': _("Moved"),
        'flag': CHANGE,
    },
    operations.DELETE_PAGE: {
        'message': _("Deleted"),
        'flag': DELETION,
    },
}

def log_page_operations(sender, **kwargs):
    """
    """

    request = kwargs.pop('request')
    operation_type = kwargs.pop('operation')
    obj = kwargs.pop('obj')

    user_id = request.user.pk
    content_type_id = ContentType.objects.get_for_model(obj).pk
    object_id = obj.pk
    object_repr = str(obj)

    operation_handler = _page_operations_map[operation_type]

    if operation_handler:
        create_log_entry(user_id, content_type_id, object_id, object_repr, operation_handler['flag'], operation_handler['message'])

def log_placeholder_operations(sender, **kwargs):
    """
    Create the log for the correct operation type
    """

    request = kwargs.pop('request')
    operation_type = kwargs.pop('operation')
    language = kwargs.pop('language')
    token = kwargs.pop('token')
    origin = kwargs.pop('origin')

    user_id = request.user.pk

    if operation_type == operations.ADD_PLUGIN:

        plugin = kwargs.pop('plugin')
        page = plugin.placeholder.page

        content_type_id = ContentType.objects.get_for_model(page).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, _("Added Plugin"))

    elif operation_type == operations.CHANGE_PLUGIN:

        plugin = kwargs.pop('new_plugin')
        page = plugin.placeholder.page

        content_type_id = ContentType.objects.get_for_model(page).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, _("Changed Plugin"))

    elif operation_type == operations.MOVE_PLUGIN:

        plugin = kwargs.pop('plugin')
        page = plugin.placeholder.page

        content_type_id = ContentType.objects.get_for_model(page).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, _("Moved Plugin"))

    elif operation_type == operations.DELETE_PLUGIN:

        plugin = kwargs.pop('plugin')
        page = plugin.placeholder.page

        content_type_id = ContentType.objects.get_for_model(page).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, _("Deleted Plugin"))

    elif operation_type == operations.CUT_PLUGIN:

        plugin = kwargs.pop('plugin')
        page = plugin.placeholder.page
        content_type_id = ContentType.objects.get_for_model(page).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, _("Cut Plugin"))

    elif operation_type == operations.PASTE_PLUGIN:
        plugin = kwargs.pop('plugin')
        page = plugin.placeholder.page
        content_type_id = ContentType.objects.get_for_model(page).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, _("Paste Plugin"))

    elif operation_type == operations.PASTE_PLACEHOLDER:

        placeholder = kwargs.pop('target_placeholder')
        page = placeholder.page

        content_type_id = ContentType.objects.get_for_model(placeholder).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, _("Paste to Placeholder"))

    elif operation_type == operations.ADD_PLUGINS_FROM_PLACEHOLDER:

        source_placeholder = kwargs.pop('source_placeholder')
        target_placeholder = kwargs.pop('target_placeholder')

        page = target_placeholder.page

        content_type_id = ContentType.objects.get_for_model(page).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, _("Added plugins to placeholder from clipboard"))

    elif operation_type == operations.CLEAR_PLACEHOLDER:

        placeholder = kwargs.pop('placeholder')
        page = placeholder.page

        content_type_id = ContentType.objects.get_for_model(page).pk
        object_id = page.pk
        object_repr = str(page)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, _("Cleared Placeholder"))