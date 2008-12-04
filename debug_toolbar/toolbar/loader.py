"""
The main DebugToolbar class that loads and renders the Toolbar.
"""
from django.template.loader import render_to_string
from debug_toolbar.settings import DEBUG_TOOLBAR_PANELS
import django

class DebugToolbar(object):
    def __init__(self, request):
        self.request = request
        self.panels = []
        self.panel_list = []
        self.content_list = []
    
    def load_panels(self):
        """
        Populate debug panel lists from settings.DEBUG_TOOLBAR_PANELS.
        """
        from django.conf import settings
        from django.core import exceptions

        for panel_path in DEBUG_TOOLBAR_PANELS:
            try:
                dot = panel_path.rindex('.')
            except ValueError:
                raise exceptions.ImproperlyConfigured, '%s isn\'t a debug panel module' % panel_path
            panel_module, panel_classname = panel_path[:dot], panel_path[dot+1:]
            try:
                mod = __import__(panel_module, {}, {}, [''])
            except ImportError, e:
                raise exceptions.ImproperlyConfigured, 'Error importing debug panel %s: "%s"' % (panel_module, e)
            try:
                panel_class = getattr(mod, panel_classname)
            except AttributeError:
                raise exceptions.ImproperlyConfigured, 'Toolbar Panel module "%s" does not define a "%s" class' % (panel_module, panel_classname)

            panel_instance = panel_class(self.request)

            self.panels.append(panel_instance)

    def render_toolbar(self):
        """
        Renders the overall Toolbar with panels inside.
        """
        context = {
            'debug_show_cookie': self.request.COOKIES.get('djDebugShow'),
            'django_version': django.get_version(),
            'panels': self.panels,
            'base_url': '/' + self.request.META['SCRIPT_NAME'],
        }
        
        return render_to_string('debug_toolbar/base.html', context)
