# -*- coding: utf-8 -*-
from __future__ import with_statement
from contextlib import contextmanager

from django.test import TestCase

from cms.api import create_page
from cms.signals import urls_need_reloading


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
        with signal_tester(urls_need_reloading) as env:
            self.client.get('/')
            self.assertEqual(env.call_count, 0)
            create_page(
                "apphooked-page",
                "nav_playground.html",
                "en",
                published=True,
                apphook="SampleApp",
                apphook_namespace="test"
            )
            self.client.get('/')
            self.assertEqual(env.call_count, 1)

    def test_urls_need_reloading_signal_delete(self):
        with signal_tester(urls_need_reloading) as env:
            self.client.get('/')
            self.assertEqual(env.call_count, 0)
            page = create_page(
                "apphooked-page",
                "nav_playground.html",
                "en",
                published=True,
                apphook="SampleApp",
                apphook_namespace="test"
            )
            page.delete()
            self.client.get('/')
            self.assertEqual(env.call_count, 1)

    def test_urls_need_reloading_signal_change_slug(self):
        with signal_tester(urls_need_reloading) as env:
            self.assertEqual(env.call_count, 0)
            page = create_page(
                "apphooked-page",
                "nav_playground.html",
                "en",
                published=True,
                apphook="SampleApp",
                apphook_namespace="test"
            )
            self.client.get('/')
            self.assertEqual(env.call_count, 1)
            title = page.title_set.get(language="en")
            title.slug += 'test'
            title.save()
            page.publish('en')
            self.client.get('/')
            self.assertEqual(env.call_count, 2)
