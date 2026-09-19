"""Helpers for performance regression tests (query and cache call counts)."""
import re
from contextlib import contextmanager
from unittest import mock

from django.core.cache import caches
from django.db import connection
from django.test.utils import CaptureQueriesContext

# Cache backend methods that cost one round trip on a networked backend.
CACHE_OPS = ("get", "set", "add", "delete", "get_many", "set_many", "delete_many", "touch", "incr")


def capture_queries():
    """Shortcut for ``CaptureQueriesContext`` on the default connection."""
    return CaptureQueriesContext(connection)


def queries_on(captured, table, verb="SELECT"):
    """
    Return the captured SQL statements of type ``verb`` that read from ``table``.

    Matches ``FROM "table"`` / ``JOIN "table"`` with any identifier quoting, so it
    works on SQLite, Postgres and MySQL. Example::

        with capture_queries() as captured:
            render()
        self.assertEqual(queries_on(captured, "cms_page"), [])
    """
    pattern = re.compile(rf'(FROM|JOIN)\s+["`]?{re.escape(table)}["`]?(\s|$|,)', re.IGNORECASE)
    return [
        query["sql"]
        for query in captured.captured_queries
        if query["sql"].lstrip("( ").upper().startswith(verb) and pattern.search(query["sql"])
    ]


class CacheCalls(list):
    """List of ``(op, key_or_keys)`` tuples, one per cache round trip."""

    def ops(self, *names):
        return [call for call in self if call[0] in names]

    def keys_containing(self, fragment, *names):
        """Calls whose key (or any key, for ``*_many``) contains ``fragment``."""
        found = []

        for op, keys in self:
            if names and op not in names:
                continue
            key_list = keys if isinstance(keys, (list, tuple, set, dict)) else [keys]

            if any(fragment in str(key) for key in key_list):
                found.append((op, keys))
        return found


@contextmanager
def count_cache_calls(alias="default"):
    """
    Record every top-level call made to the cache backend.

    Nested calls are ignored (``BaseCache.get_many`` loops over ``get``), so
    each recorded entry is what a networked backend would see as a round trip.
    """
    backend = caches[alias]
    calls = CacheCalls()
    state = {"depth": 0}

    def _wrap(op):
        original = getattr(backend, op)

        def wrapper(*args, **kwargs):
            if state["depth"] == 0:
                calls.append((op, args[0] if args else None))
            state["depth"] += 1

            try:
                return original(*args, **kwargs)
            finally:
                state["depth"] -= 1

        return wrapper

    patchers = [mock.patch.object(backend, op, _wrap(op)) for op in CACHE_OPS]

    for patcher in patchers:
        patcher.start()

    try:
        yield calls
    finally:
        for patcher in patchers:
            patcher.stop()
