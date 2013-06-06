# -*- coding: utf-8 -*-
from cms.toolbar_pool import toolbar_pool
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


@toolbar_pool.register
def category_toolbar(toolbar, request, is_current_app, app_name):
    if not toolbar.is_staff:
        return
    admin_menu = toolbar.get_menu('category', _('Category'))
    admin_menu.add_sideframe_item(_('Categories'), url=reverse('admin:sampleapp_category_changelist'))
    admin_menu.add_modal_item(_('Add Category'), url=reverse('admin:sampleapp_category_add'), close_on_url_change=True)
