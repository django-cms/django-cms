from collections import OrderedDict

from django.template.defaultfilters import force_escape


def plugin_to_tag(obj, content='', admin=False):
    plugin_attrs = OrderedDict(
        id=obj.pk,
        icon_alt=force_escape(obj.get_instance_icon_alt()),
        content=content,
    )

    if admin:
        # Include extra attributes when rendering on the admin
        plugin_class = obj.get_plugin_class()
        preview = getattr(plugin_class, 'text_editor_preview', True)
        plugin_tag = (
            u'<cms-plugin render-plugin=%(preview)s alt="%(icon_alt)s "'
            u'title="%(icon_alt)s" id="%(id)d">%(content)s</cms-plugin>'
        )
        plugin_attrs['preview'] = 'true' if preview else 'false'
    else:
        plugin_tag = (
            u'<cms-plugin alt="%(icon_alt)s "'
            u'title="%(icon_alt)s" id="%(id)d">%(content)s</cms-plugin>'
        )
    return plugin_tag % plugin_attrs
