# -*- coding: utf-8 -*-
from menus.base import Menu
from django.core.exceptions import ValidationError

class CMSAttachMenu(Menu):
    cms_enabled = True
    name = None
    
    def __init__(self, *args, **kwargs):
        super(CMSAttachMenu, self).__init__(*args, **kwargs)
        if self.cms_enabled and not self.name:
            raise ValidationError("the menu %s is a CMSAttachMenu but has no name defined!" % self.__class__.__name__)
