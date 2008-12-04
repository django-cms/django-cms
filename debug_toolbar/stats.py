try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

import inspect
import time

__all__ = ('track', 'get_stats', 'enable_tracking', 'reset_tracking', 'freeze_tracking')

class StatCollection(object):
    def __init__(self):
        self.reset()
    
    def run(self, func, key, *args, **kwargs):
        """Profile a function and store its information."""
        start_time = time.time()
        value = func(*args, **kwargs)
        end_time = time.time()
        this_time = end_time - start_time
        values = {
            'args': args,
            'kwargs': kwargs,
            'count': 0,
            'hits': 0,
            'time': 0.0
        }
        row = self.grouped.setdefault(key, {}).setdefault(func.__name__, values)
        row['count'] += 1
        row['time'] += this_time
        if value is not None:
            row['hits'] += 1
        
        self.calls.setdefault(key, []).append({
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'time': this_time,
            'hit': value is not None,
            'stack': [s[1:] for s in inspect.stack()[2:]],
        })
        row = self.summary.setdefault(key, {'count': 0, 'time': 0.0, 'hits': 0})
        row['count'] += 1
        row['time'] += this_time
        if value is not None:
            row['hits'] += 1
        
        return value
    
    def reset(self):
        """Reset the collection."""
        self.grouped = {}
        self.calls = {}
        self.summary = {}

    def get_total_time(self, key):
        return self.summary.get(key, {}).get('time', 0)

    def get_total_calls(self, key):
        return self.summary.get(key, {}).get('count', 0)

    def get_total_hits(self, key):
        return self.summary.get(key, {}).get('hits', 0)

    def get_total_misses(self, key):
        return self.get_total_calls(key)-self.get_total_hits(key)

    def get_total_hits_for_function(self, key, func):
        return self.grouped.get(key, {}).get(func.__name__, {}).get('hits', 0)

    def get_total_calls_for_function(self, key, func):
        return self.grouped.get(key, {}).get(func.__name__, {}).get('count', 0)

    def get_total_misses_for_function(self, key, func):
        return self.get_total_calls_for_function(key, func) - self.get_total_hits_for_function(key, func)

    def get_total_time_for_function(self, key, func):
        return self.grouped.get(key, {}).get(func.__name__, {}).get('time', 0)

    def get_calls(self, key):
        return self.calls.get(key, [])

_stats = local()
def get_stats():
    return _stats.collection

def enable_tracking(true_or_false):
    _stats.track = true_or_false

def reset_tracking():
    _stats.collection = StatCollection()
    _stats.track = False

def freeze_tracking():
    enable_tracking(False)

def track(func, key):
    """A decorator which handles tracking calls on a function."""
    def wrapped(*args, **kwargs):
        if _stats.track:
            return _stats.collection.run(func, key, *args, **kwargs)
        return func(*args, **kwargs)
    wrapped.__doc__ = func.__doc__
    wrapped.__name__ = func.__name__
    return wrapped