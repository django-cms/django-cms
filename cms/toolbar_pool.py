from collections import OrderedDict

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import autodiscover_modules, import_string

from cms.exceptions import ToolbarAlreadyRegistered, ToolbarNotRegistered
from cms.utils.conf import get_cms_setting


class ToolbarPool:
    def __init__(self):
        self.toolbars = OrderedDict()
        self._discovered = False
        self.force_register = False

    def discover_toolbars(self):
        if self._discovered:
            return
            # import all the modules
        toolbars = get_cms_setting('TOOLBARS')
        if toolbars:
            for path in toolbars:
                cls = import_string(path)
                self.force_register = True
                self.register(cls)
                self.force_register = False
        else:
            autodiscover_modules('cms_toolbars')
        self._discovered = True

    def clear(self):
        self.toolbars = OrderedDict()
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
        return sum((list(getattr(tb, 'watch_models', []))
                    for tb in self.toolbars.values()), [])


toolbar_pool = ToolbarPool()
