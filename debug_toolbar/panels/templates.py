from debug_toolbar.panels import DebugPanel
from django.conf import settings
from django.dispatch import dispatcher
from django.core.signals import request_started
from django.test.signals import template_rendered
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from django import template

from debug_toolbar.stats import track, get_stats

template.Template.render = track(template.Template.render, 'templates:django')

try:
    import jinja2
except ImportError:
    pass
else:
    jinja2.Environment.get_template = track(jinja2.Environment.get_template, 'templates:jinja2')

try:
    import jinja
except ImportError:
    pass
else:
    jinja.Environment.get_template = track(jinja.Environment.get_template, 'templates:jinja')

class TemplatesDebugPanel(DebugPanel):
    """
    Panel that displays information about the SQL queries run while processing the request.
    """
    name = 'Templates'
    engine_list = ('django', 'jinja', 'jinja2')
    
    def process_ajax(self, request):
        action = request.GET.get('op')
        if action == 'explain':
            return render_to_response('debug_toolbar/panels/templates_explain.html')

    def do_stat_call(self, name):
        result = None
        for t in self.engine_list:
            r = getattr(get_stats(), name)('templates:%s' % (t,))
            if result:
                result += r
            else:
                result = r
        return result

    def title(self):
        return 'Templates: %d' % (self.do_stat_call('get_total_calls'),)

    def url(self):
        return ''

    def content(self):
        context = dict(
            template_calls = self.do_stat_call('get_total_calls'),
            template_time = self.do_stat_call('get_total_time'),
            template_calls_list = [(c['time'], c['args'][1], 'jinja2', c['stack']) for c in get_stats().get_calls('templates:jinja2')] + \
                    [(c['time'], c['args'][1], 'jinja', c['stack']) for c in get_stats().get_calls('templates:jinja')] + \
                    [(c['time'], c['args'][0].name, 'django', c['stack']) for c in get_stats().get_calls('templates:django')],
        )
        return render_to_string('debug_toolbar/panels/templates.html', context)