from debug_toolbar.panels import DebugPanel
from django.template.loader import render_to_string

class RequestVarsDebugPanel(DebugPanel):
    """
    A panel to display HTTP variables (POST/GET).
    """
    name = 'HttpVars'
    # List of headers we want to display

    def title(self):
        return 'Request Variables'

    def url(self):
        return ''

    def content(self):
        context = {
            'get': [(k, self.request.GET.getlist(k)) for k in self.request.GET.iterkeys()],
            'post': [(k, self.request.POST.getlist(k)) for k in self.request.POST.iterkeys()],
            'session': [(k, self.request.session.get(k)) for k in self.request.session.iterkeys()],
            'cookies': [(k, self.request.COOKIES.get(k)) for k in self.request.COOKIES.iterkeys()],
        }
        return render_to_string('debug_toolbar/panels/request_vars.html', context)