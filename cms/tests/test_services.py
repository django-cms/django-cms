from cms.api import add_plugin, create_page
from cms.core.services import plugins as plugin_services
from cms.shared.operations import OperationContext
from cms.signals import post_placeholder_operation, pre_placeholder_operation
from cms.test_utils.testcases import CMSTestCase


class OperationContextTest(CMSTestCase):
    def test_from_request_parses_the_originating_path(self):
        request = self.get_request("/en/admin/cms/placeholder/?cms_path=/en/some-page/")
        request.user = self.get_superuser()

        context = OperationContext.from_request(request)

        self.assertEqual(context.origin, "/en/some-page/")
        self.assertEqual(context.language, "en")
        self.assertIs(context.request, request)
        self.assertTrue(context.emit_signals)

    def test_language_query_on_the_origin_wins(self):
        """``?language`` lets an editor view one language at another's URL."""
        request = self.get_request("/en/admin/?cms_path=/en/some-page/%3Flanguage%3Dde")
        request.user = self.get_superuser()
        request.GET = request.GET.copy()
        request.GET["cms_path"] = "/en/some-page/?language=de"

        self.assertEqual(OperationContext.from_request(request).language, "de")

    def test_placeholder_request_without_cms_path_stays_silent(self):
        """The long-standing shim: no cms_path means no operation signals."""
        request = self.get_request("/en/admin/cms/placeholder/")
        request.user = self.get_superuser()

        with self.assertWarns(UserWarning):
            context = OperationContext.from_placeholder_request(request)

        self.assertFalse(context.emit_signals)
        self.assertIsNone(context.origin)

    def test_plain_request_without_cms_path_still_emits(self):
        """Only the placeholder endpoints use cms_path; page endpoints do not."""
        request = self.get_request("/en/admin/cms/page/1/set-home/")
        request.user = self.get_superuser()

        context = OperationContext.from_request(request)

        self.assertTrue(context.emit_signals)
        self.assertIsNone(context.origin)


class RequestFreeServiceTest(CMSTestCase):
    """Services run outside the admin -- no request, no HTTP, no admin instance."""

    def setUp(self):
        super().setUp()
        self.user = self.get_superuser()
        self.page = create_page("home", "nav_playground.html", "en")
        self.placeholder = self.page.get_placeholders("en").get(slot="body")

    def _context(self, **kwargs):
        return OperationContext(user=self.user, language="en", origin="/en/", **kwargs)

    def test_move_plugin_without_a_request(self):
        first = add_plugin(self.placeholder, "LinkPlugin", "en", name="first")
        second = add_plugin(self.placeholder, "LinkPlugin", "en", name="second")

        plugin_services.move_plugin(
            second.cmsplugin_ptr,
            target_position=1,
            context=self._context(),
        )

        order = self.placeholder.get_plugin_tree_order(language="en")
        self.assertEqual(order, [second.pk, first.pk])

    def test_signals_fire_with_request_none(self):
        """Receivers get ``request=None`` for a programmatic call, and must cope."""
        plugin = add_plugin(self.placeholder, "LinkPlugin", "en", name="one")
        seen = []

        def receiver(sender, **kwargs):
            seen.append(kwargs)

        pre_placeholder_operation.connect(receiver, dispatch_uid="svc-test-pre")
        post_placeholder_operation.connect(receiver, dispatch_uid="svc-test-post")
        try:
            plugin_services.move_plugin(plugin.cmsplugin_ptr, target_position=1, context=self._context())
        finally:
            pre_placeholder_operation.disconnect(dispatch_uid="svc-test-pre")
            post_placeholder_operation.disconnect(dispatch_uid="svc-test-post")

        self.assertEqual(len(seen), 2)
        for kwargs in seen:
            self.assertIsNone(kwargs["request"])
            self.assertEqual(kwargs["origin"], "/en/")
            self.assertEqual(kwargs["language"], "en")
        self.assertEqual(seen[0]["token"], seen[1]["token"])

    def test_silenced_context_emits_nothing(self):
        plugin = add_plugin(self.placeholder, "LinkPlugin", "en", name="one")
        seen = []
        pre_placeholder_operation.connect(lambda sender, **kw: seen.append(kw), dispatch_uid="svc-test-quiet")
        try:
            plugin_services.move_plugin(
                plugin.cmsplugin_ptr,
                target_position=1,
                context=self._context(emit_signals=False),
            )
        finally:
            pre_placeholder_operation.disconnect(dispatch_uid="svc-test-quiet")

        self.assertEqual(seen, [])

    def test_delete_plugin_without_a_request(self):
        plugin = add_plugin(self.placeholder, "LinkPlugin", "en", name="doomed")

        tree_order = plugin_services.delete_plugin(plugin.cmsplugin_ptr, context=self._context())

        self.assertEqual(tree_order, [])
        self.assertFalse(self.placeholder.get_plugins("en").exists())

    def test_clear_placeholder_without_a_request(self):
        add_plugin(self.placeholder, "LinkPlugin", "en", name="one")
        add_plugin(self.placeholder, "LinkPlugin", "en", name="two")

        plugin_services.clear_placeholder(self.placeholder, "en", context=self._context())

        self.assertFalse(self.placeholder.get_plugins("en").exists())
