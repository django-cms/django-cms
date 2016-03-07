# -*- coding: utf-8 -*-
from contextlib import contextmanager

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings

from cms.api import create_page
from cms.models import UrlconfRevision
from cms.signals import urls_need_reloading
from cms.test_utils.project.sampleapp.cms_apps import SampleApp
from cms.test_utils.util.context_managers import apphooks
from cms.test_utils.testcases import CMSTestCase


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
        with apphooks(SampleApp):
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
        with apphooks(SampleApp):
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
        with apphooks(SampleApp):
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


@override_settings(
    MIDDLEWARE_CLASSES=[
        'cms.middleware.utils.ApphookReloadMiddleware'
    ] + settings.MIDDLEWARE_CLASSES,
)
class ApphooksReloadTests(CMSTestCase):
    def test_urls_reloaded(self):
        """
        Tests that URLs are automatically reloaded when the ApphookReload
        middleware is installed.
        """
        #
        # Sets up an apphook'ed page, but does not yet publish it.
        #
        superuser = get_user_model().objects.create_superuser(
            'admin', 'admin@admin.com', 'admin')
        page = create_page("home", "nav_playground.html", "en",
                           created_by=superuser)
        page.publish('en')
        app_page = create_page("app_page", "nav_playground.html", "en",
                               created_by=superuser, parent=page,
                               published=False, apphook="SampleApp")
        self.client.get('/')  # Required to invoke the middleware
        #
        # Gets the current urls revision for testing against later.
        #
        current_revision, _ = UrlconfRevision.get_or_create_revision()

        #
        # Publishes the apphook. This is one of many ways to trigger the
        # firing of the signal. The tests above test some of the other ways
        # already.
        #
        app_page.publish('en')
        self.client.get('/')  # Required to invoke the middleware

        # And, this should result in a the updating of the UrlconfRevision
        new_revision, _ = UrlconfRevision.get_or_create_revision()
        self.assertNotEquals(current_revision, new_revision)
