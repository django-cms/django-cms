# -*- coding: utf-8 -*-
from cms.exceptions import ToolbarAlreadyRegistered
from cms.utils.conf import get_cms_setting
from cms.utils.django_load import load, iterload_objects
from django.core.exceptions import ImproperlyConfigured


class ToolbarPool(object):
    def __init__(self):
        self.toolbars = {}
        self.reverse = {}
        self.discovered = False
        self.block_register = False

    def discover_toolbars(self):
        if self.discovered:
            return
            #import all the modules
        toolbars = get_cms_setting('TOOLBARS')
        if toolbars:
            self.block_register = True
            for cls in iterload_objects(toolbars):
                self.block_register = False
                self.register(cls)
                self.block_register = True
            self.block_register = False
        else:
            load('cms_toolbar')
        self.discovered = True

    def clear(self):
        self.apps = {}
        self.discovered = False

    def register(self, toolbar):
        if self.block_register:
            return
        from cms.toolbar_base import CMSToolbar
        # validate the app
        if not issubclass(toolbar, CMSToolbar):
            raise ImproperlyConfigured('CMS Toolbar must inherit '
                                       'cms.toolbar_base.CMSToolbar, %r does not' % toolbar)
        name = "%s.%s" % (toolbar.__module__, toolbar.__name__)
        if name in self.toolbars.keys():
            raise ToolbarAlreadyRegistered("[%s] a toolbar with this name is already registered" % name)
        self.toolbars[name] = toolbar

    def get_toolbars(self):
        self.discover_toolbars()
        return self.toolbars

toolbar_pool = ToolbarPool()
