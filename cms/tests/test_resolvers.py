from cms.api import create_page
from cms.models import Placeholder
from cms.shared.resolvers import provide, providers, resolve
from cms.test_utils.testcases import CMSTestCase


class ResolverRegistryTest(CMSTestCase):
    def test_unprovided_lookup_returns_the_default(self):
        """A container keeps working when the one that would answer is absent."""
        self.assertIsNone(resolve("no_such_lookup", 1, 2))
        self.assertEqual(resolve("no_such_lookup", default="fallback"), "fallback")

    def test_provide_registers_and_replaces(self):
        provide("test_lookup", lambda value: f"first:{value}")
        self.assertEqual(resolve("test_lookup", "x"), "first:x")

        provide("test_lookup", lambda value: f"second:{value}")
        self.assertEqual(resolve("test_lookup", "x"), "second:x")

    def test_arguments_are_forwarded(self):
        provide("test_args", lambda *args, **kwargs: (args, kwargs))
        self.assertEqual(resolve("test_args", 1, 2, key="value"), ((1, 2), {"key": "value"}))

    def test_providers_is_a_copy(self):
        providers()["injected"] = object()
        self.assertNotIn("injected", providers())


class PlaceholderPageResolverTest(CMSTestCase):
    """``Placeholder.page`` is answered by pages, not computed by core.

    Core no longer imports ``PageContent``; if the registration in
    ``cms.models.contentmodels`` ever stops running, nothing raises -- every
    placeholder would just quietly report no page. Hence these tests.
    """

    def test_lookup_is_registered(self):
        self.assertIn("placeholder_page", providers())

    def test_page_placeholder_resolves_to_its_page(self):
        page = create_page("home", "nav_playground.html", "en")
        placeholder = page.get_placeholders("en").first()

        # Re-fetch so the generic foreign key is not already cached, exercising
        # the query path rather than the shortcut.
        self.assertEqual(Placeholder.objects.get(pk=placeholder.pk).page, page)

    def test_page_placeholder_resolves_via_cached_source(self):
        page = create_page("home", "nav_playground.html", "en")
        placeholder = page.get_placeholders("en").select_related("content_type").first()
        placeholder.source  # prime the generic foreign key cache

        self.assertEqual(placeholder.page, page)

    def test_placeholder_without_a_source_has_no_page(self):
        self.assertIsNone(Placeholder.objects.create(slot="detached").page)

    def test_page_setter_still_overrides(self):
        page = create_page("home", "nav_playground.html", "en")
        placeholder = Placeholder.objects.create(slot="detached")

        placeholder.page = page

        self.assertEqual(placeholder.page, page)
