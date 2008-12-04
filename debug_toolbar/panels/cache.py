from debug_toolbar.panels import DebugPanel
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.core.cache import cache

from debug_toolbar.stats import track, get_stats

# Track stats on these function calls
cache.set = track(cache.set, 'cache')
cache.get = track(cache.get, 'cache')
cache.delete = track(cache.delete, 'cache')
cache.add = track(cache.add, 'cache')
cache.get_many = track(cache.get_many, 'cache')

class CacheDebugPanel(DebugPanel):
    """
    Panel that displays the cache statistics.
    """
    name = 'Cache'

    def process_ajax(self, request):
        action = request.GET.get('op')
        if action == 'explain':
            return render_to_response('debug_toolbar/panels/cache_explain.html')

    def title(self):
        return 'Cache: %.2fms' % get_stats().get_total_time('cache')

    def url(self):
        return ''

    def has_content(self):
        return bool(get_stats().get_total_calls('cache'))

    def content(self):
        context = dict(
            cache_calls = get_stats().get_total_calls('cache'),
            cache_time = get_stats().get_total_time('cache'),
            cache_hits = get_stats().get_total_hits('cache'),
            cache_misses = get_stats().get_total_misses_for_function('cache', cache.get) + get_stats().get_total_misses_for_function('cache', cache.get_many),
            cache_gets = get_stats().get_total_calls_for_function('cache', cache.get),
            cache_sets = get_stats().get_total_calls_for_function('cache', cache.set),
            cache_get_many = get_stats().get_total_calls_for_function('cache', cache.get_many),
            cache_deletes = get_stats().get_total_calls_for_function('cache', cache.delete),
            cache_calls_list = [(c['time'], c['func'].__name__, c['args'], c['kwargs'], simplejson.dumps(c['stack'])) for c in get_stats().get_calls('cache')],
        )
        return render_to_string('debug_toolbar/panels/cache.html', context)