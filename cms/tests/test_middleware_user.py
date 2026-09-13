import contextvars
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.signals import request_finished
from django.http import HttpResponse
from django.test import AsyncClient, SimpleTestCase, override_settings
from django.urls import path
from django.utils.asyncio import async_unsafe
from django.utils.functional import SimpleLazyObject

from cms.signals.apphook import DISPATCH_UID, set_restart_trigger, trigger_restart
from cms.utils.permissions import (
    _current_user,
    current_user,
    get_current_user,
    get_current_user_name,
    reset_current_user,
    set_current_user,
)


@async_unsafe
def sync_only_user(request):
    """Stands in for an auth backend that hits the database."""
    return AnonymousUser()


async def health(request):
    return HttpResponse("ok")


urlpatterns = [path("health/", health)]


class CurrentUserContextTests(SimpleTestCase):
    def test_set_and_get_round_trip(self):
        user = AnonymousUser()
        token = set_current_user(user)
        try:
            self.assertIs(get_current_user(), user)
        finally:
            reset_current_user(token)
        self.assertIsNone(get_current_user())

    def test_none_round_trip(self):
        token = set_current_user(None)
        try:
            self.assertIsNone(get_current_user())
            self.assertEqual(get_current_user_name(), "script")
        finally:
            reset_current_user(token)

    def test_context_manager(self):
        user = AnonymousUser()
        with current_user(user):
            self.assertIs(get_current_user(), user)
        self.assertIsNone(get_current_user())

    def test_lazy_user_survives_context_comparison(self):
        """The stored value must be comparable without waking the lazy user.

        asgiref restores context variables by comparing their values
        (``asgiref.sync._restore_context``). When that comparison happens on
        the event loop thread, evaluating a lazy ``request.user`` runs the
        auth backend's query there and raises ``SynchronousOnlyOperation``.
        """
        evaluated = []

        def evaluate():
            evaluated.append(True)
            return AnonymousUser()

        lazy_user = SimpleLazyObject(evaluate)
        token = set_current_user(lazy_user)
        try:
            context = contextvars.copy_context()
            self.assertFalse(_current_user.get() != context.get(_current_user))
            self.assertEqual(evaluated, [])
            self.assertIs(get_current_user(), lazy_user)
            self.assertEqual(evaluated, [])
        finally:
            reset_current_user(token)


@override_settings(
    ROOT_URLCONF=__name__,
    MIDDLEWARE=[
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "cms.middleware.user.CurrentUserMiddleware",
    ],
    SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
)
class CurrentUserMiddlewareAsyncTests(SimpleTestCase):
    """Regression tests for #8859: ASGI requests hung on a lazy user."""

    def setUp(self):
        # Another test may have armed the apphook restart trigger, which hits
        # the database from request_finished and is unrelated to this test.
        # Disarm it for the duration of the test and re-arm it afterwards so
        # the signal is left exactly as it was found.
        was_armed = request_finished.disconnect(trigger_restart, dispatch_uid=DISPATCH_UID)
        if was_armed:
            self.addCleanup(set_restart_trigger)

    async def test_asgi_request_with_unevaluated_lazy_user(self):
        with patch("django.contrib.auth.middleware.get_user", sync_only_user):
            response = await AsyncClient().get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    async def test_current_user_does_not_leak_between_requests(self):
        with patch("django.contrib.auth.middleware.get_user", sync_only_user):
            await AsyncClient().get("/health/")
        self.assertIsNone(get_current_user())
