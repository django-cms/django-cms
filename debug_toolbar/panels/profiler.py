from debug_toolbar.panels import DebugPanel
try: import cProfile as profile
except ImportError: import profile
import pstats
from django.template.loader import render_to_string

class ProfilerDebugPanel(DebugPanel):
    """
    Panel that displays the time a response took with cProfile output.
    """
    name = 'Profiler'

    def __init__(self, request):
        super(ProfilerDebugPanel, self).__init__(request)
    
    def has_content(self):
        return bool(self.profiler)
    
    def process_request(self, request):
        self.profiler = None
    
    def process_response(self, request, response):
        if self.profiler is not None:
            stats = pstats.Stats(self.profiler)
            function_calls = []
            for func in stats.strip_dirs().sort_stats(1).fcn_list:
                current = []
                if stats.stats[func][0] != stats.stats[func][1]:
                    current.append('%d/%d' % (stats.stats[func][1], stats.stats[func][0]))
                else:
                    current.append(stats.stats[func][1])
                current.append(stats.stats[func][2]*1000)
                if stats.stats[func][1]:
                    current.append(stats.stats[func][2]*1000/stats.stats[func][1])
                else:
                    current.append(0)
                current.append(stats.stats[func][3]*1000)
                if stats.stats[func][0]:
                    current.append(stats.stats[func][3]*1000/stats.stats[func][0])
                else:
                    current.append(0)
                current.append(pstats.func_std_string(func))
                function_calls.append(current)
            self.stats = stats
            self.function_calls = function_calls
            # destroy the profiler just in case
        return response

    def process_view(self, request, callback, callback_args, callback_kwargs):
        self.callback = callback
        self.profiler = profile.Profile()
        return self.profiler.runcall(callback, request, *callback_args, **callback_kwargs)
        
    def title(self):
        return 'View: %.2fms' % (float(self.stats.total_tt)*1000,)

    def url(self):
        return ''

    def content(self):
        context = {
            'callback': self.callback.__name__,
            'module': self.callback.__module__,
            'stats': self.stats,
            'function_calls': self.function_calls,
        }
        return render_to_string('debug_toolbar/panels/profiler.html', context)