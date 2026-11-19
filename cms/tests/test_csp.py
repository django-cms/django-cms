"""Tests for Content Security Policy nonce support in django CMS templates.

Django 6.1 introduced a built-in ``{% csp_nonce_attr %}`` tag. django CMS ships
its own implementation in ``cms_static`` so that the very same templates render
on Django 5.2 and 6.0, where the built-in does not exist.
"""
import re
import unittest
from copy import deepcopy

from django.conf import settings
from django.forms import Media
from django.template import Context, Template, TemplateSyntaxError
from django.test.utils import override_settings
from django.urls import clear_url_caches

from cms.api import add_plugin, create_page
from cms.templatetags.cms_static import CSP_NONCE_SUPPORTED
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.utils import get_object_edit_url
from cms.utils.urlutils import admin_reverse

NONCE = "cms-test-nonce"

#: Matches ``nonce="..."`` on any element.
NONCE_RE = re.compile(r'nonce="([^"]*)"')
#: Matches the nonce echoed back in the ``Content-Security-Policy`` header.
HEADER_NONCE_RE = re.compile(r"'nonce-([^']+)'")
#: Matches an opening ``<script>``/``<link>``/``<style>`` tag with its attributes.
ASSET_TAG_RE = re.compile(r"<(script|link|style)\b([^>]*)>", re.IGNORECASE)
#: Everything django CMS itself ships is served from below this prefix.
CMS_STATIC_PREFIX = "/static/cms/"

requires_csp = unittest.skipUnless(CSP_NONCE_SUPPORTED, "Django < 6.1 has no CSP nonce support")


def render_template(template_string, **context):
    return Template("{% load cms_static %}" + template_string).render(Context(context))


def csp_overrides():
    """Settings that turn on Django 6.1's nonce-based CSP for the test project."""
    from django.utils.csp import CSP

    templates = deepcopy(settings.TEMPLATES)
    templates[0]["OPTIONS"]["context_processors"].append("django.template.context_processors.csp")
    return {
        "TEMPLATES": templates,
        "MIDDLEWARE": ["django.middleware.csp.ContentSecurityPolicyMiddleware", *settings.MIDDLEWARE],
        "SECURE_CSP": {
            "default-src": [CSP.SELF],
            "script-src": [CSP.SELF, CSP.NONCE],
            "style-src": [CSP.SELF, CSP.NONCE],
        },
    }


class CspNonceTagTests(CMSTestCase):
    """Unit tests for the ``cms_static`` template tags."""

    def setUp(self):
        super().setUp()
        self.media = Media(css={"screen": ["cms/css/test.css"]}, js=["cms/js/test.js"])

    def test_nonce_attr_renders_nothing_without_a_nonce(self):
        self.assertHTMLEqual(
            render_template("<script src='x' {% csp_nonce_attr %}></script>"),
            "<script src='x'></script>",
        )

    def test_media_renders_without_a_nonce(self):
        rendered = render_template("{% csp_nonce_attr media %}", media=self.media)
        self.assertIn("cms/css/test.css", rendered)
        self.assertIn("cms/js/test.js", rendered)
        self.assertNotIn("nonce=", rendered)

    def test_render_media_assets_returns_one_string_per_asset(self):
        for media_type, expected in (("css", "cms/css/test.css"), ("js", "cms/js/test.js")):
            with self.subTest(media_type=media_type):
                rendered = render_template(
                    '{%% render_media_assets media "%s" as assets %%}'
                    "{%% for asset in assets %%}[{{ asset }}]{%% endfor %%}" % media_type,
                    media=self.media,
                )
                self.assertEqual(rendered.count("["), 1)
                self.assertIn(expected, rendered)

    def test_render_media_assets_rejects_unknown_media_type(self):
        with self.assertRaises(TemplateSyntaxError):
            render_template('{% render_media_assets media "images" as assets %}', media=self.media)

    @requires_csp
    def test_nonce_attr_renders_the_nonce(self):
        self.assertHTMLEqual(
            render_template("<script src='x' {% csp_nonce_attr %}></script>", csp_nonce=NONCE),
            f"<script src='x' nonce='{NONCE}'></script>",
        )

    @requires_csp
    def test_media_carries_the_nonce(self):
        rendered = render_template("{% csp_nonce_attr media %}", media=self.media, csp_nonce=NONCE)
        self.assertEqual(NONCE_RE.findall(rendered), [NONCE, NONCE])

    @requires_csp
    def test_render_media_assets_carries_the_nonce(self):
        for media_type in ("css", "js"):
            with self.subTest(media_type=media_type):
                rendered = render_template(
                    '{%% render_media_assets media "%s" as assets %%}'
                    "{%% for asset in assets %%}{{ asset }}{%% endfor %%}" % media_type,
                    media=self.media,
                    csp_nonce=NONCE,
                )
                self.assertEqual(NONCE_RE.findall(rendered), [NONCE])


class NonceAssertionsMixin:
    """Helpers shared by the view level tests.

    Only django CMS' own assets -- everything served from ``/static/cms/`` -- are
    asserted on. Django's admin templates nonce their assets themselves, and
    assets contributed by third party apps or by the project's own templates are
    outside django CMS' control.
    """

    def assertNoNonces(self, response):
        self.assertNotIn("nonce=", response.content.decode())

    def get_header_nonce(self, response):
        """Return the nonce the CSP middleware put in the response header."""
        policy = response.headers["Content-Security-Policy"]
        nonces = set(HEADER_NONCE_RE.findall(policy))
        self.assertEqual(len(nonces), 1, f"expected exactly one nonce in {policy!r}")
        return nonces.pop()

    def get_cms_asset_tags(self, response):
        """Yield the attribute strings of every nonce-relevant ``/static/cms/`` tag.

        ``<link>`` elements that are not stylesheets -- favicons, for instance --
        are governed by ``img-src`` rather than ``style-src`` and take no nonce.
        """
        return [
            attributes
            for tag, attributes in ASSET_TAG_RE.findall(response.content.decode())
            if CMS_STATIC_PREFIX in attributes
            and not (tag.lower() == "link" and 'rel="stylesheet"' not in attributes)
        ]

    def assertCmsAssetsAreNonced(self, response, minimum=1):
        """Every django CMS asset must carry the response's nonce.

        Non-executable ``<script type="application/json">`` data blocks are
        exempt: browsers never run them, so CSP never checks them, and Django's
        own ``json_script()`` leaves them bare.
        """
        nonce = self.get_header_nonce(response)
        tags = self.get_cms_asset_tags(response)

        for attributes in tags:
            self.assertIn(
                f'nonce="{nonce}"',
                attributes,
                f"<... {attributes.strip()}> is missing the CSP nonce",
            )

        self.assertGreaterEqual(
            len(tags), minimum, f"expected at least {minimum} django CMS asset(s) in the response"
        )
        return tags

    def assertJsonBlocksAreNonceFree(self, response):
        json_tags = [
            attributes
            for tag, attributes in ASSET_TAG_RE.findall(response.content.decode())
            if tag.lower() == "script" and 'type="application/json"' in attributes
        ]
        self.assertGreater(len(json_tags), 0, "expected JSON data blocks in the response")
        for attributes in json_tags:
            self.assertNotIn("nonce=", attributes, "JSON data blocks must not carry a nonce")


@requires_csp
class CspNonceAdminViewTests(NonceAssertionsMixin, CMSTestCase):
    """django CMS admin pages must emit the request nonce on their own assets."""

    def setUp(self):
        super().setUp()
        self.page = create_page("home", "nav_playground.html", "en")
        self.superuser = self.get_superuser()

    def test_page_tree(self):
        with override_settings(**csp_overrides()):
            with self.login_user_context(self.superuser):
                response = self.client.get(self.get_pages_admin_list_uri())
        self.assertEqual(response.status_code, 200)
        self.assertCmsAssetsAreNonced(response)

    def test_page_change_form(self):
        with override_settings(**csp_overrides()):
            with self.login_user_context(self.superuser):
                response = self.client.get(self.get_page_change_uri("en", self.page))
        self.assertEqual(response.status_code, 200)
        self.assertCmsAssetsAreNonced(response)

    def test_plugin_change_form(self):
        placeholder = self.page.get_placeholders("en").get(slot="body")
        plugin = add_plugin(placeholder, "LinkPlugin", "en", name="link", external_link="http://example.com")
        with override_settings(**csp_overrides()):
            with self.login_user_context(self.superuser):
                response = self.client.get(self.get_change_plugin_uri(plugin))
        self.assertEqual(response.status_code, 200)
        self.assertCmsAssetsAreNonced(response)

    def test_usersettings_change_form(self):
        with override_settings(**csp_overrides()):
            with self.login_user_context(self.superuser):
                response = self.client.get(admin_reverse("cms_usersettings_change", args=(self.superuser.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertCmsAssetsAreNonced(response)

    def test_page_delete_confirmation(self):
        """The delete confirmation carries django CMS' only inline ``<style>``.

        It has no ``href``, so it is checked by hand rather than through
        :meth:`assertCmsAssetsAreNonced`.
        """
        with override_settings(**csp_overrides()):
            with self.login_user_context(self.superuser):
                response = self.client.get(self.get_admin_url(type(self.page), "delete", self.page.pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<style nonce="{self.get_header_nonce(response)}">')

    def test_wizard(self):
        with override_settings(**csp_overrides()):
            with self.login_user_context(self.superuser):
                response = self.client.get(admin_reverse("cms_wizard_create"))
        self.assertEqual(response.status_code, 200)
        self.assertCmsAssetsAreNonced(response)


@requires_csp
class CspNonceToolbarViewTests(NonceAssertionsMixin, CMSTestCase):
    """The toolbar injects its assets into arbitrary front end pages."""

    def setUp(self):
        super().setUp()
        clear_url_caches()
        self.superuser = self.get_superuser()

    def tearDown(self):
        super().tearDown()
        clear_url_caches()

    def get_edit_response(self, page):
        with override_settings(**csp_overrides()):
            with self.login_user_context(self.superuser):
                return self.client.get(get_object_edit_url(page.get_content_obj("en"), "en"))

    def test_toolbar_on_a_cms_page(self):
        response = self.get_edit_response(create_page("home", "nav_playground.html", "en"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cms-config-json")
        self.assertCmsAssetsAreNonced(response)
        self.assertJsonBlocksAreNonceFree(response)

    def test_toolbar_assets_carry_the_nonce(self):
        """The toolbar's assets are emitted one at a time through sekizai.

        ``cms.text.css`` comes from the toolbar's ``Media`` and therefore
        exercises ``{% render_media_assets %}``; the other two are plain tags.
        """
        response = self.get_edit_response(create_page("home", "nav_playground.html", "en"))
        nonce = self.get_header_nonce(response)
        content = response.content.decode()
        for asset in ("cms.base.css", "bundle.toolbar.min.js", "djangocms_text/css/cms.text.css"):
            with self.subTest(asset=asset):
                tag = next(
                    (attrs for _, attrs in ASSET_TAG_RE.findall(content) if asset in attrs),
                    None,
                )
                self.assertIsNotNone(tag, f"{asset} is missing from the response")
                self.assertIn(f'nonce="{nonce}"', tag)

    def test_welcome_page(self):
        with override_settings(**csp_overrides()):
            response = self.client.get("/en/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, "cms/welcome.html")
        self.assertCmsAssetsAreNonced(response)


class NoCspConfiguredTests(NonceAssertionsMixin, CMSTestCase):
    """Without CSP configured no ``nonce`` attribute may appear anywhere.

    These run on every supported Django version, and are the regression test
    for templates referencing a tag that does not exist below Django 6.1.
    """

    def setUp(self):
        super().setUp()
        clear_url_caches()
        self.page = create_page("home", "nav_playground.html", "en")
        self.superuser = self.get_superuser()

    def tearDown(self):
        super().tearDown()
        clear_url_caches()

    def test_admin_views_render_without_nonces(self):
        endpoints = {
            "page tree": self.get_pages_admin_list_uri(),
            "page change form": self.get_page_change_uri("en", self.page),
            "usersettings": admin_reverse("cms_usersettings_change", args=(self.superuser.pk,)),
            "wizard": admin_reverse("cms_wizard_create"),
            "delete confirmation": self.get_admin_url(type(self.page), "delete", self.page.pk),
        }
        with self.login_user_context(self.superuser):
            for name, endpoint in endpoints.items():
                with self.subTest(view=name):
                    response = self.client.get(endpoint)
                    self.assertEqual(response.status_code, 200)
                    self.assertNoNonces(response)

    def test_toolbar_renders_without_nonces(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(get_object_edit_url(self.page.get_content_obj("en"), "en"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cms-config-json")
        self.assertNoNonces(response)

    def test_welcome_page_renders_without_nonces(self):
        self.page.delete()
        response = self.client.get("/en/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, "cms/welcome.html")
        self.assertNoNonces(response)
