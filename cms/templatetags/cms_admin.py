"""The ``cms_admin`` template library.

This module stays where it is: Django finds template libraries by app-relative
path, so ``{% load cms_admin %}`` names *this* module and always will. Despite
its name it is mostly page-tree chrome, not frontend editing; the definitions
now live with the container that owns them:

=============================================== ================================
``{% show_admin_menu_for_pages %}``,
``{% get_page_display_name %}``,
``{% tree_publish_row %}``,
``{% tree_publish_row_menu %}``,
``{% render_filter_field %}``,
``{% page_submit_row %}``, ``|in_filtered``,
``{% get_admin_url_for_language %}``               :mod:`cms.pages.admin.templatetags`
``{% submit_row_plugin %}``,
``|placeholder_is_immutable``                      :mod:`cms.core.admin.templatetags`
``{% get_preview_url %}``, ``{% get_edit_url %}``,
``{% django_version_gte %}``,
``{% admin_fieldset %}``, ``|boolean_icon``,
``{% admin_static_url %}``,
``{% cms_admin_icon_base %}``                      :mod:`cms.shared.admin_templatetags`
=============================================== ================================

The full tag set is registered below, so nothing changes for a template author.
This module also re-exports the tag classes and functions, because third-party
code imports them from here.
"""

from django import template

from cms.core.admin.templatetags import placeholder_is_immutable, submit_row_plugin
from cms.pages.admin.templatetags import (
    GetAdminUrlForLanguage,
    PageSubmitRow,
    TreePublishRow,
    TreePublishRowMenu,
    get_page_display_name,
    in_filtered,
    render_filter_field,
    show_admin_menu_for_pages,
)
from cms.shared.admin_templatetags import (  # noqa: F401  -- re-exported
    CMS_ADMIN_ICON_BASE,
    CMSAdminIconBase,
    GetEditUrl,
    GetPreviewUrl,
    admin_fieldset,
    admin_static_url,
    boolean_icon,
    django_version_gte,
)

register = template.Library()

# -- pages: the page tree and the page forms --------------------------------
register.simple_tag(show_admin_menu_for_pages, takes_context=True)
register.simple_tag(get_page_display_name, takes_context=False)
register.tag(TreePublishRow.name, TreePublishRow)
register.tag(TreePublishRowMenu.name, TreePublishRowMenu)
register.inclusion_tag("admin/cms/page/tree/filter.html")(render_filter_field)
register.tag(PageSubmitRow.name, PageSubmitRow)
register.filter("in_filtered", in_filtered)
register.tag(GetAdminUrlForLanguage.name, GetAdminUrlForLanguage)

# -- core: plugins and placeholders -----------------------------------------
register.inclusion_tag("admin/cms/page/plugin/submit_line.html", takes_context=True)(submit_row_plugin)
register.filter("placeholder_is_immutable", placeholder_is_immutable)

# -- shared: editing URLs and admin chrome ----------------------------------
register.tag(GetPreviewUrl.name, GetPreviewUrl)
register.tag(GetEditUrl.name, GetEditUrl)
register.simple_tag(django_version_gte)
register.simple_tag(admin_fieldset)
register.filter("boolean_icon", boolean_icon)
register.simple_tag(admin_static_url)
register.tag(CMSAdminIconBase.name, CMSAdminIconBase)
