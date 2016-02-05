# -*- coding: utf-8 -*-
from cms.exceptions import ToolbarAlreadyRegistered, ToolbarNotRegistered
from cms.utils.conf import get_cms_setting
from cms.utils.django_load import load, iterload_objects
from django.core.exceptions import ImproperlyConfigured

try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict


class ToolbarPool(object):
    def __init__(self):
        self.toolbars = OrderedDict()
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
            # FIXME: Remove in 3.4
            load('cms_toolbar')
            load('cms_toolbars')
        self._discovered = True

    def clear(self):
        self.toolbars = OrderedDict()
        self._discovered = False

    def register(self, toolbar):
        import warnings
        if toolbar.__module__.split('.')[-1] == 'cms_toolbar':
            warnings.warn('cms_toolbar.py filename is deprecated, '
                          'and it will be removed in version 3.4; '
                          'please rename it to cms_toolbars.py', DeprecationWarning)
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
        return sum((list(getattr(tb, 'watch_models', []))
                    for tb in self.toolbars.values()), [])


toolbar_pool = ToolbarPool()
