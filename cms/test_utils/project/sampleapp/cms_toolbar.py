# -*- coding: utf-8 -*-
from cms.toolbar.items import List, Item
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


class CategoryToolbar(CMSToolbar):
    def insert_items(self, items, toolbar, request, is_app):
        if toolbar.is_staff:
            items[0].items = [Item(reverse('admin:sampleapp_category_changelist'), _('Categories'),
                                   load_side_frame=True)] + items[0].items
            if is_app:
                cat_list = List(reverse('admin:sampleapp_category_changelist'), _('Category'))
                cat_list.items.append(Item(reverse('admin:sampleapp_category_add'), _("Add Category")))
                items.append(cat_list)


toolbar_pool.register(CategoryToolbar)