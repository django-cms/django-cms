"""Admin templatetags of the placeholder/plugin core.

The plugin change form's submit row and the structure board's read-only test.
Registered by :mod:`cms.templatetags.cms_admin`.
"""

from cms.core.models.placeholder import Placeholder


def submit_row_plugin(context):
    """
    Displays the row of buttons for delete and save.
    """
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']
    ctx = {
        'opts': opts,
        'show_delete_link': context.get(
            'has_delete_permission', False) and change and context.get('show_delete', True),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and not is_popup and (
            not save_as or context['add']),
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'preserved_filters': context.get('preserved_filters'),
    }
    if context.get('original') is not None:
        ctx['original'] = context['original']
    return ctx


def placeholder_is_immutable(placeholder, user):
    if isinstance(placeholder, Placeholder):
        # A placeholder is editable only if the source permits editing *and*
        # the user may change it. View-only users (e.g. headless reviewers) can
        # open the structure board but must see it read-only.
        return not (placeholder.check_source(user) and placeholder.has_change_permission(user))
    return True
