"""Toolbar state lookup, plus shims for the names that moved out of this module.

This module used to hold three unrelated things: structure-mode plugin
serialisation, the frontend-editing URL contract, and toolbar state. Only the
last is about the toolbar; the other two are now in
:mod:`cms.core.editing.structure` and :mod:`cms.shared.editing_urls`.

That mattered beyond tidiness: twelve modules across every container imported
this file, almost all of them only to build an edit URL, which is why ``menus``
appeared to depend on the toolbar.

Every moved name keeps working from here (see :mod:`cms.compat`).
"""

from django.http import HttpRequest

from cms.compat import moved


def get_toolbar_from_request(request: HttpRequest):
    from .toolbar import EmptyToolbar

    return getattr(request, "toolbar", EmptyToolbar(request))


__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        # -> core.editing (structure-mode payloads)
        "create_child_plugin_references": "cms.core.editing.structure.create_child_plugin_references",
        "get_placeholder_toolbar_js": "cms.core.editing.structure.get_placeholder_toolbar_js",
        "get_plugin_content": "cms.core.editing.structure.get_plugin_content",
        "get_plugin_toolbar_info": "cms.core.editing.structure.get_plugin_toolbar_info",
        "get_plugin_toolbar_js": "cms.core.editing.structure.get_plugin_toolbar_js",
        "get_plugin_tree": "cms.core.editing.structure.get_plugin_tree",
        "get_plugin_tree_ids": "cms.core.editing.structure.get_plugin_tree_ids",
        # -> shared (frontend-editing URL contract)
        "_get_object_url": "cms.shared.editing_urls._get_object_url",
        "add_live_url_querystring_param": "cms.shared.editing_urls.add_live_url_querystring_param",
        "get_object_edit_url": "cms.shared.editing_urls.get_object_edit_url",
        "get_object_for_language": "cms.shared.editing_urls.get_object_for_language",
        "get_object_live_url": "cms.shared.editing_urls.get_object_live_url",
        "get_object_preview_url": "cms.shared.editing_urls.get_object_preview_url",
        "get_object_structure_url": "cms.shared.editing_urls.get_object_structure_url",
    },
    since="5.2",
)

# ``moved()`` returns only the relocated names; this module still defines one.
__all__.append("get_toolbar_from_request")
__all__.sort()
