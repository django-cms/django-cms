# -*- coding: utf-8 -*-
from cms.exceptions import ToolbarAlreadyRegistered, ToolbarNotRegistered
from cms.utils.conf import get_cms_setting
from cms.utils.django_load import load, iterload_objects
from django.core.exceptions import ImproperlyConfigured
from django.utils.datastructures import SortedDict


class ToolbarPool(object):
    def __init__(self):
        self.toolbars = SortedDict()
        self._discovered = False
        self.force_register = False

    def discover_toolbars(self):
        if self._discovered:
            return
            #import all the modules
        toolbars = get_cms_setting('TOOLBARS')
        if toolbars:
            for cls in iterload_objects(toolbars):
                self.force_register = True
                self.register(cls)
                self.force_register = False
        else:
            load('cms_toolbar')
        self._discovered = True

    def clear(self):
        self.toolbars = SortedDict()
        self._discovered = False

    def register(self, toolbar):
        if not self.force_register and get_cms_setting('TOOLBARS'):
            return toolbar
        from cms.toolbar_base import CMSToolbar
        # validate the app
        if not issubclass(toolbar, CMSToolbar):
            raise ImproperlyConfigured('CMS Toolbar must inherit '
                                       'cms.toolbar_base.CMSToolbar, %r does not' % toolbar)
        name = "%s.%s" % (toolbar.__module__, toolbar.__name__)
        if name in self.toolbars.keys():
            raise ToolbarAlreadyRegistered("[%s] a toolbar with this name is already registered" % name)
        self.toolbars[name] = toolbar
        return toolbar

    def unregister(self, toolbar):
        name = '%s.%s' % (toolbar.__module__, toolbar.__name__)
        if name not in self.toolbars:
            raise ToolbarNotRegistered('The toolbar %s is not registered' % name)
        del self.toolbars[name]

    def get_toolbars(self):
        self.discover_toolbars()
        return self.toolbars

    def get_watch_models(self):
        models = []
        for toolbar in self.toolbars.values():
            if hasattr(toolbar, 'watch_models'):
                models += toolbar.watch_models
        return models


toolbar_pool = ToolbarPool()
