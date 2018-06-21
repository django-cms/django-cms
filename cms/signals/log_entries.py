from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION

from django.contrib.contenttypes.models import ContentType


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


def log_page_operations(sender, **kwargs):
    """

    # Get the operation type
    find_operation = operations.PAGE_OPERATIONS.index(operation_type)
    handler = operations.PAGE_OPERATIONS[find_operation]
    """


    request = kwargs.pop('request')
    operation_type = kwargs.pop('operation')
    obj = kwargs.pop('obj')

    user_id = request.user.pk
    content_type_id = ContentType.objects.get_for_model(obj).pk
    object_id = obj.pk
    object_repr = str(obj)

    if operation_type == operations.ADD_PAGE:
        create_log_entry(user_id, content_type_id, object_id, object_repr, ADDITION, "Added")
    elif operation_type == operations.MOVE_PAGE:
        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, "Moved")
    elif operation_type == operations.CHANGE_PAGE:
        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, "Change")
    elif operation_type == operations.DELETE_PAGE:
        create_log_entry(user_id, content_type_id, object_id, object_repr, DELETION, "Deleted")
    else:
        return


# FIXME: This is very repetitive and ugly
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
        content_type_id = ContentType.objects.get_for_model(plugin).pk
        object_id = plugin.pk
        object_repr = str(plugin)

        create_log_entry(user_id, content_type_id, object_id, object_repr, ADDITION, "Added Plugin")

    elif operation_type == operations.CHANGE_PLUGIN:

        plugin = kwargs.pop('new_plugin')
        content_type_id = ContentType.objects.get_for_model(plugin).pk
        object_id = plugin.pk
        object_repr = str(plugin)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, "Changed Plugin")

    elif operation_type == operations.MOVE_PLUGIN:

        plugin = kwargs.pop('plugin')
        content_type_id = ContentType.objects.get_for_model(plugin).pk
        object_id = plugin.pk
        object_repr = str(plugin)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, "Moved Plugin")

    elif operation_type == operations.DELETE_PLUGIN:

        plugin = kwargs.pop('plugin')
        content_type_id = ContentType.objects.get_for_model(plugin).pk
        object_id = plugin.pk
        object_repr = str(plugin)

        create_log_entry(user_id, content_type_id, object_id, object_repr, DELETION, "Deleted Plugin")

    elif operation_type == operations.CUT_PLUGIN:

        plugin = kwargs.pop('plugin')
        content_type_id = ContentType.objects.get_for_model(plugin).pk
        object_id = plugin.pk
        object_repr = str(plugin)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, "Cut Plugin")

    elif operation_type == operations.PASTE_PLUGIN:

        plugin = kwargs.pop('plugin')
        content_type_id = ContentType.objects.get_for_model(plugin).pk
        object_id = plugin.pk
        object_repr = str(plugin)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, "Paste Plugin")



    elif operation_type == operations.PASTE_PLACEHOLDER:

        placeholder = kwargs.pop('target_placeholder')
        content_type_id = ContentType.objects.get_for_model(placeholder).pk
        object_id = placeholder.pk
        object_repr = str(placeholder)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, "Paste Placeholder")

    elif operation_type == operations.ADD_PLUGINS_FROM_PLACEHOLDER:

        source_placeholder = kwargs.pop('source_placeholder')
        target_placeholder = kwargs.pop('target_placeholder')

        placeholder = target_placeholder

        content_type_id = ContentType.objects.get_for_model(placeholder).pk
        object_id = placeholder.pk
        object_repr = str(placeholder)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, "Added Plugins to Placeholder")

    elif operation_type == operations.CLEAR_PLACEHOLDER:

        placeholder = kwargs.pop('placeholder')
        content_type_id = ContentType.objects.get_for_model(placeholder).pk
        object_id = placeholder.pk
        object_repr = str(placeholder)

        create_log_entry(user_id, content_type_id, object_id, object_repr, CHANGE, "Cleared Placeholder")