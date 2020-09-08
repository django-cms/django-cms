from django.template.loader import get_template
from django.utils.functional import cached_property


class TemplatesCache:

    def __init__(self):
        self._cached_templates = {}

    def get_cached_template(self, template):
        # we check if template quacks like a Template, as generic Template and engine-specific Template
        # does not share a common ancestor
        if hasattr(template, 'render'):
            return template

        if not template in self._cached_templates:
            # this always return a engine-specific template object
            self._cached_templates[template] = get_template(template)
        return self._cached_templates[template]

    @cached_property
    def drag_item_template(self):
        return get_template('cms/toolbar/dragitem.html')

    @cached_property
    def placeholder_plugin_menu_template(self):
        return get_template('cms/toolbar/dragitem_menu.html')

    @cached_property
    def dragbar_template(self):
        return get_template('cms/toolbar/dragbar.html')
