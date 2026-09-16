"""The ``cms_tags`` template library.

This module stays where it is: Django finds template libraries by app-relative
path, so ``{% load cms_tags %}`` names *this* module and always will. What moved
is the tag definitions, which now live with the container that owns them:

=============================================== ================================
``{% placeholder %}``, ``{% render_placeholder %}``,
``{% render_uncached_placeholder %}``, ``{% render_plugin_block %}``,
``{% render_plugin %}``, ``{% render_extra_menu_items %}``,
``{% render_model %}`` and its variants            :mod:`cms.core.editing.templatetags`
``{% page_url %}``, ``{% page_id_url %}``,
``{% page_attribute %}``, ``{% show_placeholder %}``,
``{% show_uncached_placeholder %}``                :mod:`cms.pages.templatetags`
``{% cms_toolbar %}``                              :mod:`cms.toolbar.templatetags`
``{% cms_admin_url %}``                            :mod:`cms.shared.templatetags`
=============================================== ================================

The full tag set is registered below, so nothing changes for a template author.
This module also re-exports the tag classes and their helpers, because
third-party code imports them from here.
"""

from django import template

from cms.core.editing.templatetags import (  # noqa: F401  -- re-exported, see below
    NULL,
    CMSEditableObject,
    CMSEditableObjectAdd,
    CMSEditableObjectAddBlock,
    CMSEditableObjectBlock,
    CMSEditableObjectIcon,
    DeclaredPlaceholder,
    Placeholder,
    PlaceholderOptions,
    PlaceholderParser,
    RenderPlaceholder,
    RenderPluginBlock,
    RenderUncachedPlaceholder,
    render_extra_menu_items,
    render_plugin,
)
from cms.pages.templatetags import (
    PageAttribute,
    PageUrl,
    _get_page_by_untyped_arg,  # noqa: F401  -- re-exported
    _show_placeholder_by_id,
    _show_uncached_placeholder_by_id,
)
from cms.shared.templatetags import (  # noqa: F401  -- re-exported
    CMSAdminURL,
    EmptyListValue,
    MultiValueArgumentBeforeKeywordArgument,
)
from cms.toolbar.templatetags import CMSToolbar

register = template.Library()

# -- core: placeholders, plugins and the generic model editor ---------------
register.tag("placeholder", Placeholder)
register.tag("render_placeholder", RenderPlaceholder)
register.tag("render_uncached_placeholder", RenderUncachedPlaceholder)
register.tag("render_plugin_block", RenderPluginBlock)
register.tag("render_model", CMSEditableObject)
register.tag("render_model_block", CMSEditableObjectBlock)
register.tag("render_model_add", CMSEditableObjectAdd)
register.tag("render_model_add_block", CMSEditableObjectAddBlock)
register.tag("render_model_icon", CMSEditableObjectIcon)
register.simple_tag(render_extra_menu_items, takes_context=True, name="render_extra_menu_items")
register.simple_tag(render_plugin, takes_context=True, name="render_plugin")

# -- pages ------------------------------------------------------------------
register.tag("page_url", PageUrl)
register.tag("page_id_url", PageUrl)
register.tag("page_attribute", PageAttribute)
register.simple_tag(_show_placeholder_by_id, takes_context=True, name="show_placeholder")
register.simple_tag(_show_placeholder_by_id, takes_context=True, name="show_placeholder_by_id")
register.simple_tag(
    _show_uncached_placeholder_by_id, takes_context=True, name="show_uncached_placeholder"
)
register.simple_tag(
    _show_uncached_placeholder_by_id, takes_context=True, name="show_uncached_placeholder_by_id"
)

# -- toolbar and shared -----------------------------------------------------
register.tag("cms_toolbar", CMSToolbar)
register.tag("cms_admin_url", CMSAdminURL)
