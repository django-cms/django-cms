# -*- coding: utf-8 -*-
from cms.toolbar.items import List, Item
from cms.toolbar_base import CMSToolbar
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

class CategoryToolbar(CMSToolbar):
    def insert_items(self, items, toolbar, request, is_app):
        if toolbar.is_staff:
            items[0].items.append(
                Item(reverse('admin:sampleapp_category_changelist'), _('Categories'), load_side_frame=True))
            if is_app:
                cat_list = List(reverse('admin:sampleapp_category_changelist'), _('Category'))
                cat_list.items.append(Item(reverse('admin:sampleapp_category_add'), _("Add Category")))
            admin_items = List(reverse("admin:index"), _("Admin"))
        admin_items.items.append(Item(reverse('admin:index'), _('Administration'), load_side_frame=True))
        if self.can_change:
            admin_items.items.append(Item(reverse("admin:cms_page_changelist"), _('Pages'), load_side_frame=True))
        if self.request.user.has_perm('user.change_user'):
            admin_items.items.append(Item(reverse("admin:auth_user_changelist"), _('Users'), load_side_frame=True))
