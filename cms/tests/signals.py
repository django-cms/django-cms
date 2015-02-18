# -*- coding: utf-8 -*-
from __future__ import with_statement
from contextlib import contextmanager

from django.test import TestCase

from cms.api import create_page
from cms.signals import urls_need_reloading
from cms.utils.compat.dj import get_user_model


class SignalTester(object):
    def __init__(self):
        self.call_count = 0
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.calls.append((args, kwargs))


@contextmanager
def signal_tester(signal):
    env = SignalTester()
    signal.connect(env, weak=True)
    try:
        yield env
    finally:
        signal.disconnect(env, weak=True)
    


class SignalTests(TestCase):
    def test_urls_need_reloading_signal_create(self):
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        with signal_tester(urls_need_reloading) as env:
            create_page("apphooked-page", "nav_playground.html", "en",
                created_by=superuser, published=True, apphook="SampleApp")
            self.client.get('/')
            self.assertEqual(env.call_count, 1)

    def test_urls_need_reloading_signal_delete(self):
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        page = create_page("apphooked-page", "nav_playground.html", "en",
            created_by=superuser, published=True, apphook="SampleApp")
        with signal_tester(urls_need_reloading) as env:
            page.delete()
            self.client.get('/')
            self.assertEqual(env.call_count, 1)
