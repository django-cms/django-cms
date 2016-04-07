# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK
from cms.toolbar.items import Break
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.urlutils import admin_reverse

from .models import Example1, CharPksExample

SAMPLEAPP_BREAK = 'Example1 App Break'


@toolbar_pool.register
class Example1Toolbar(CMSToolbar):
    watch_models = (Example1, CharPksExample)

    def populate(self):
        admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        position = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)
        if position:
            position -= 1
        else:
            position = 0
        category_menu = admin_menu.get_or_create_menu('example', _('Example1'), position=position)
        category_menu.add_sideframe_item(_('Examples'), url=admin_reverse('placeholderapp_example1_changelist'))
