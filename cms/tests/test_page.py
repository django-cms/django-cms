# -*- coding: utf-8 -*-
import datetime
import os.path
import functools
from unittest import skipIf

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import reverse
from django.utils.timezone import now as tz_now
from django.utils.translation import override as force_language

from cms import constants
from cms.api import create_page, add_plugin, create_title, publish_page
from cms.exceptions import PublicIsUnmodifiable, PublicVersionNeeded
from cms.forms.validators import validate_url_uniqueness
from cms.models import Page, Title
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.sitemaps import CMSSitemap
from cms.test_utils.testcases import CMSTestCase, TransactionCMSTestCase
from cms.utils.conf import get_cms_setting
from cms.utils.page import (
    get_available_slug,
    get_current_site,
    get_page_from_request,
)


class PageMigrationTestCase(CMSTestCase):

    def test_content_type(self):
        """
        Test correct content type is set for Page object
        """
        from django.contrib.contenttypes.models import ContentType
        self.assertEqual(ContentType.objects.filter(model='page', app_label='cms').count(), 1)


def has_no_custom_user():
    return get_user_model().USERNAME_FIELD != 'email'


class PagesTestCase(TransactionCMSTestCase):

    def tearDown(self):
        cache.clear()

    def test_absolute_url(self):
        user = self.get_superuser()
        page = self.create_homepage("page", "nav_playground.html", "en", published=True)
        create_title("fr", "french home", page)
        page_2 = create_page("inner", "nav_playground.html", "en", published=True, parent=page)
        create_title("fr", "french inner", page_2)
        publish_page(page_2, user, "fr")

        self.assertEqual(page_2.get_absolute_url(), '/en/inner/')
        self.assertEqual(page_2.get_absolute_url(language='en'), '/en/inner/')
        self.assertEqual(page_2.get_absolute_url(language='fr'), '/fr/french-inner/')

        with force_language('fr'):
            self.assertEqual(page_2.get_absolute_url(), '/fr/french-inner/')
            self.assertEqual(page_2.get_absolute_url(language='en'), '/en/inner/')
            self.assertEqual(page_2.get_absolute_url(language='fr'), '/fr/french-inner/')

    def test_get_root_page(self):
        _create = functools.partial(
            create_page,
            template='nav_playground.html',
            language='en',
            published=True,
        )
        page_a = _create('page_a')
        page_a_a = _create('page_a_a_a', parent=page_a)
        page_a_a_a = _create('page_a_a_a', parent=page_a_a)
        page_tree_with_root = [
            (page_a, page_a),
            (page_a_a, page_a),
            (page_a_a_a, page_a),
        ]

        for page, root in page_tree_with_root:
            self.assertEqual(page.get_root(), root)
            self.assertEqual(page.publisher_public.get_root(), root.publisher_public)

    def test_treebeard_delete(self):
        """
        This is a test for #4102

        When deleting a page, parent must be updated too, to reflect the new tree status.
        This is handled by MP_NodeQuerySet (which was not used before the fix)

        """
        page1 = create_page('home', 'nav_playground.html', 'en', published=True)
        page2 = create_page('page2', 'nav_playground.html', 'en', parent=page1, published=True)
        page3 = create_page('page3', 'nav_playground.html', 'en', parent=page2, published=True)

        self.assertEqual(page1.node.depth, 1)
        self.assertEqual(page1.node.numchild, 1)
        self.assertFalse(page1.node.is_leaf())

        self.assertEqual(page2.node.depth, 2)
        self.assertEqual(page2.node.numchild, 1)
        self.assertFalse(page2.node.is_leaf())

        self.assertEqual(page3.node.depth, 3)
        self.assertEqual(page3.node.numchild, 0)
        self.assertTrue(page3.node.is_leaf())

        page3.delete()
        page1 = page1.reload().get_draft_object()
        page2 = page2.reload().get_draft_object()

        self.assertEqual(page2.node.depth, 2)
        self.assertEqual(page2.node.numchild, 0)
        self.assertTrue(page2.node.is_leaf())

        page3 = create_page('page3', 'nav_playground.html', 'en', parent=page2, reverse_id='page3')

        self.assertEqual(page2.node.depth, 2)
        self.assertEqual(page2.node.numchild, 1)
        self.assertFalse(page2.node.is_leaf())

        self.assertEqual(page3.node.depth, 3)
        self.assertEqual(page3.node.numchild, 0)
        self.assertTrue(page3.node.is_leaf())

        page1.publish('en')
        page2.publish('en')
        page3.publish('en')

        self.assertEqual(page1.node.depth, 1)
        self.assertEqual(page1.node.numchild, 1)
        self.assertFalse(page1.node.is_leaf())

        self.assertEqual(page2.node.depth, 2)
        self.assertEqual(page2.node.numchild, 1)
        self.assertFalse(page2.node.is_leaf())

        self.assertEqual(page3.node.depth, 3)
        self.assertEqual(page3.node.numchild, 0)
        self.assertTrue(page3.node.is_leaf())

    def test_create_page_api(self):
        page_data = {
            'title': 'root',
            'slug': 'root',
            'language': settings.LANGUAGES[0][0],
            'template': 'nav_playground.html',

        }
        page = self.create_homepage(**page_data)
        page = page.reload()
        page.publish('en')
        self.assertEqual(Page.objects.count(), 2)
        self.assertTrue(page.is_home)
        self.assertTrue(page.publisher_public.is_home)

        self.assertEqual(list(Title.objects.drafts().values_list('path', flat=True)), [u''])
        self.assertEqual(list(Title.objects.public().values_list('path', flat=True)), [u''])

    @skipIf(has_no_custom_user(), 'No custom user')
    def test_create_page_api_with_long_username(self):
        page_data = {
            'title': 'root',
            'slug': 'root',
            'language': settings.LANGUAGES[0][0],
            'template': 'nav_playground.html',
            'created_by': self._create_user(
                'V' * constants.PAGE_USERNAME_MAX_LENGTH + 'ERY-LONG-USERNAME',
                is_staff=True,
                is_superuser=True,
            ),
        }
        page = create_page(**page_data)
        self.assertEqual(Page.objects.count(), 1)

        self.assertLessEqual(len(page.created_by), constants.PAGE_USERNAME_MAX_LENGTH)
        self.assertRegexpMatches(page.created_by, r'V+\.{3} \(id=\d+\)')

        self.assertLessEqual(len(page.changed_by), constants.PAGE_USERNAME_MAX_LENGTH)
        self.assertRegexpMatches(page.changed_by, r'V+\.{3} \(id=\d+\)')

        self.assertEqual(list(Title.objects.drafts().values_list('path', flat=True)), [u'root'])

    def test_delete_page_no_template(self):
        page_data = {
            'title': 'root',
            'slug': 'root',
            'language': settings.LANGUAGES[0][0],
            'template': 'nav_playground.html',

        }
        page = create_page(**page_data)
        page.template = 'no_such_template.html'
        page.delete()

        self.assertEqual(Page.objects.count(), 0)

    def test_get_available_slug_recursion(self):
        """ Checks cms.utils.page.get_available_slug for infinite recursion
        """
        site = get_current_site()
        for x in range(0, 12):
            create_page('test copy', 'nav_playground.html', 'en', published=True)
        new_slug = get_available_slug(site, 'test-copy', 'en')
        self.assertTrue(new_slug, 'test-copy-11')

    def test_path_collisions_api_1(self):
        """ Checks for slug collisions on sibling pages - uses API to create pages
        """
        site = get_current_site()
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)
        page1_1 = create_page('test page 1_1', 'nav_playground.html', 'en',
                              published=True, parent=page1, slug="foo")
        page1_2 = create_page('test page 1_2', 'nav_playground.html', 'en',
                              published=True, parent=page1, slug="foo")
        # both sibling pages has same slug, so both pages have an invalid slug
        self.assertRaises(
            ValidationError,
            validate_url_uniqueness,
            site=site,
            path=page1_1.get_path('en'),
            language='en',
            exclude_page=page1_1,
        )
        self.assertRaises(
            ValidationError,
            validate_url_uniqueness,
            site=site,
            path=page1_2.get_path('en'),
            language='en',
            exclude_page=page1_2,
        )

    def test_path_collisions_api_2(self):
        """ Checks for slug collisions on root (not home) page and a home page child - uses API to create pages
        """
        site = get_current_site()
        page1 = self.create_homepage('test page 1', 'nav_playground.html', 'en',
                            published=True)
        page1_1 = create_page('test page 1_1', 'nav_playground.html', 'en',
                              published=True, parent=page1, slug="foo")
        page2 = create_page('test page 1_1', 'nav_playground.html', 'en',
                            published=True, slug="foo")
        # Root (non home) page and child page has the same slug, both are invalid
        self.assertRaises(
            ValidationError,
            validate_url_uniqueness,
            site=site,
            path=page1_1.get_path('en'),
            language='en',
            exclude_page=page1_1,
        )
        self.assertRaises(
            ValidationError,
            validate_url_uniqueness,
            site=site,
            path=page2.get_path('en'),
            language='en',
            exclude_page=page2,
        )

    def test_path_collisions_api_3(self):
        """ Checks for slug collisions on children of a non root page - uses API to create pages
        """
        site = get_current_site()
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)
        page1_1 = create_page('test page 1_1', 'nav_playground.html', 'en',
                              published=True, parent=page1, slug="foo")
        page1_1_1 = create_page('test page 1_1_1', 'nav_playground.html', 'en',
                                published=True, parent=page1_1, slug="bar")
        page1_1_2 = create_page('test page 1_1_1', 'nav_playground.html', 'en',
                                published=True, parent=page1_1, slug="bar")
        page1_2 = create_page('test page 1_2', 'nav_playground.html', 'en',
                              published=True, parent=page1, slug="bar")
        # Direct children of home has different slug so it's ok.
        self.assertTrue(validate_url_uniqueness(
            site,
            path=page1_1.get_path('en'),
            language='en',
            exclude_page=page1_1,
        ))
        self.assertTrue(validate_url_uniqueness(
            site,
            path=page1_2.get_path('en'),
            language='en',
            exclude_page=page1_2,
        ))
        # children of page1_1 has the same slug -> you lose!
        self.assertRaises(
            ValidationError,
            validate_url_uniqueness,
            site=site,
            path=page1_1_1.get_path('en'),
            language='en',
            exclude_page=page1_1_1,
        )
        self.assertRaises(
            ValidationError,
            validate_url_uniqueness,
            site=site,
            path=page1_1_2.get_path('en'),
            language='en',
            exclude_page=page1_1_2,
        )

    def test_details_view(self):
        """
        Test the details view
        """
        superuser = self.get_superuser()
        self.assertEqual(Page.objects.all().count(), 0)
        with self.login_user_context(superuser):
            page = self.create_homepage('test page 1', "nav_playground.html", "en")
            page.publish('en')
            response = self.client.get(self.get_pages_root())
            self.assertEqual(response.status_code, 200)
            self.assertTrue(page.publish('en'))
            page2 = create_page("test page 2", "nav_playground.html", "en",
                                parent=page, published=True)
            homepage = Page.objects.get_home()
            self.assertTrue(homepage.get_slug(), 'test-page-1')

            self.assertEqual(page2.get_absolute_url(), '/en/test-page-2/')
            response = self.client.get(page2.get_absolute_url())
            self.assertEqual(response.status_code, 200)

    def test_public_exceptions(self):
        page_a = create_page("page_a", "nav_playground.html", "en", published=True)
        page_b = create_page("page_b", "nav_playground.html", "en")
        page = page_a.publisher_public
        self.assertRaises(PublicIsUnmodifiable, page.copy_with_descendants, page_b, 'last-child')
        self.assertRaises(PublicIsUnmodifiable, page.unpublish, 'en')
        self.assertRaises(PublicIsUnmodifiable, page.revert_to_live, 'en')
        self.assertRaises(PublicIsUnmodifiable, page.publish, 'en')

        self.assertTrue(page.get_draft_object().publisher_is_draft)
        self.assertRaises(PublicVersionNeeded, page_b.revert_to_live, 'en')

    def test_move_page_regression_left_to_right_5752(self):
        # ref: https://github.com/divio/django-cms/issues/5752
        # Tests tree integrity when moving sibling pages from left
        # to right under the same parent.
        home = create_page("Home", "nav_playground.html", "en", published=True)
        alpha = create_page(
            "Alpha",
            "nav_playground.html",
            "en",
            published=True,
            parent=home,
        )
        beta = create_page(
            "Beta",
            "nav_playground.html",
            "en",
            published=True,
            parent=home,
        )
        beta.move_page(alpha.node, position='left')

        # Draft
        self.assertEqual(home.node.path, '0001')
        self.assertEqual(beta.node.path, '00010001')
        self.assertEqual(alpha.node.path, '00010002')

    def test_move_page_regression_right_to_left_5752(self):
        # ref: https://github.com/divio/django-cms/issues/5752
        # Tests tree integrity when moving sibling pages from right
        # to left under the same parent.
        home = create_page("Home", "nav_playground.html", "en", published=True)
        alpha = create_page(
            "Alpha",
            "nav_playground.html",
            "en",
            published=True,
            parent=home,
        )
        beta = create_page(
            "Beta",
            "nav_playground.html",
            "en",
            published=True,
            parent=home,
        )
        beta.move_page(alpha.node, position='left')

        alpha.refresh_from_db()
        beta.refresh_from_db()

        # Draft
        self.assertEqual(home.node.path, '0001')
        self.assertEqual(beta.node.path, '00010001')
        self.assertEqual(alpha.node.path, '00010002')

    def test_move_page_regression_5640(self):
        # ref: https://github.com/divio/django-cms/issues/5640
        alpha = create_page("Alpha", "nav_playground.html", "en", published=True)
        beta = create_page("Beta", "nav_playground.html", "en", published=False)
        alpha.move_page(beta.node, position='right')
        self.assertEqual(beta.node.path, '0002')
        self.assertEqual(alpha.node.path, '0003')

    def test_move_page_regression_nested_5640(self):
        # ref: https://github.com/divio/django-cms/issues/5640
        alpha = create_page("Alpha", "nav_playground.html", "en", published=True)
        beta = create_page("Beta", "nav_playground.html", "en", published=False)
        gamma = create_page("Gamma", "nav_playground.html", "en", published=False)
        delta = create_page("Delta", "nav_playground.html", "en", published=True)
        theta = create_page("Theta", "nav_playground.html", "en", published=True)

        beta.move_page(alpha.node, position='last-child')
        gamma.move_page(beta.reload().node, position='last-child')
        delta.move_page(gamma.reload().node, position='last-child')
        theta.move_page(delta.reload().node, position='last-child')

        tree = [
            (alpha, '0001'),
            (beta, '00010001'),
            (gamma, '000100010001'),
            (delta, '0001000100010001'),
            (theta, '00010001000100010001'),
        ]

        for page, path in tree:
            self.assertEqual(page.reload().node.path, path)

    def test_move_page_regression_5643(self):
        # ref: https://github.com/divio/django-cms/issues/5643
        alpha = create_page("Alpha", "nav_playground.html", "en", published=True)
        beta = create_page("Beta", "nav_playground.html", "en", published=False)
        gamma = create_page("Gamma", "nav_playground.html", "en", published=False)
        delta = create_page("Delta", "nav_playground.html", "en", published=True)
        theta = create_page("Theta", "nav_playground.html", "en", published=True)

        beta.move_page(alpha.node, position='last-child')
        gamma.move_page(beta.node, position='last-child')
        delta.move_page(gamma.node, position='last-child')
        theta.move_page(delta.node, position='last-child')

        self.assertPublished(alpha.reload())
        self.assertNeverPublished(beta.reload())
        self.assertNeverPublished(gamma.reload())
        self.assertPending(delta.reload())
        self.assertPending(theta.reload())

    def test_publish_page_regression_5642(self):
        # ref: https://github.com/divio/django-cms/issues/5642
        alpha = create_page("Alpha", "nav_playground.html", "en", published=True)
        beta = create_page("Beta", "nav_playground.html", "en", published=False)
        gamma = create_page("Gamma", "nav_playground.html", "en", published=False)
        delta = create_page("Delta", "nav_playground.html", "en", published=True)
        theta = create_page("Theta", "nav_playground.html", "en", published=True)

        beta.move_page(alpha.node, position='last-child')
        gamma.move_page(beta.reload().node, position='last-child')
        delta.move_page(gamma.reload().node, position='last-child')
        theta.move_page(delta.reload().node, position='last-child')

        beta.reload().publish('en')

        # The delta and theta pages should remain pending publication
        # because gamma is still unpublished

        self.assertPublished(beta.reload())
        self.assertNeverPublished(gamma.reload())
        self.assertPending(delta.reload())
        self.assertPending(theta.reload())

        gamma.reload().publish('en')

        self.assertPublished(gamma.reload())
        self.assertPublished(delta.reload())
        self.assertPublished(theta.reload())

    def test_publish_page_regression_6188(self):
        # ref: https://github.com/divio/django-cms/issues/6188
        page = create_page("en-page", "nav_playground.html", "en", published=False)
        create_title('de', 'de-page', page)
        create_title('fr', 'fr-page', page)

        # Publishing the en language should set "en" as the only language
        # on the public version of the page.
        page.publish("en")

        self.assertListEqual(sorted(page.publisher_public.get_languages()), ['en'])

        page.publish("de")

        # Now there should be "en" and "de" on the public page
        self.assertSequenceEqual(sorted(page.publisher_public.get_languages()), ['de', 'en'])

        page.publish("fr")

        # Now there should be "en", "de" and "fr" on the public page
        self.assertSequenceEqual(sorted(page.publisher_public.get_languages()), ['de', 'en', 'fr'])

    def test_move_page_inherit(self):
        parent = create_page("Parent", 'col_three.html', "en")
        child = create_page("Child", constants.TEMPLATE_INHERITANCE_MAGIC,
                            "en", parent=parent)
        self.assertEqual(child.get_template(), parent.get_template())
        child.move_page(parent.node, 'left')
        child = Page.objects.get(pk=child.pk)
        self.assertEqual(child.get_template(), parent.get_template())

    def test_add_placeholder(self):
        # create page
        page = create_page("Add Placeholder", "nav_playground.html", "en",
                           position="last-child", published=True, in_navigation=True)
        page.template = 'add_placeholder.html'
        page.save()
        page.publish('en')
        url = page.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        path = os.path.join(settings.TEMPLATES[0]['DIRS'][0], 'add_placeholder.html')
        with open(path, 'r') as fobj:
            old = fobj.read()
        try:
            new = old.replace(
                '<!-- SECOND_PLACEHOLDER -->',
                '{% placeholder second_placeholder %}'
            )
            with open(path, 'w') as fobj:
                fobj.write(new)
            response = self.client.get(url)
            self.assertEqual(200, response.status_code)
        finally:
            with open(path, 'w') as fobj:
                fobj.write(old)

    def test_sitemap_login_required_pages(self):
        """
        Test that CMSSitemap object contains only published,public (login_required=False) pages
        """
        create_page("page", "nav_playground.html", "en", login_required=True,
                    published=True, in_navigation=True)
        self.assertEqual(CMSSitemap().items().count(), 0)

    def test_sitemap_includes_last_modification_date(self):
        one_day_ago = tz_now() - datetime.timedelta(days=1)
        page = create_page("page", "nav_playground.html", "en", published=True, publication_date=one_day_ago)
        page.creation_date = one_day_ago
        page.save()
        page.publish('en')
        sitemap = CMSSitemap()
        self.assertEqual(sitemap.items().count(), 1)
        actual_last_modification_time = sitemap.lastmod(sitemap.items()[0])
        self.assertTrue(actual_last_modification_time > one_day_ago)

    def test_sitemap_uses_publication_date_when_later_than_modification(self):
        now = tz_now()
        now -= datetime.timedelta(microseconds=now.microsecond)
        one_day_ago = now - datetime.timedelta(days=1)
        page = create_page("page", "nav_playground.html", "en", published=True, publication_date=now)
        title = page.get_title_obj('en')
        page.creation_date = one_day_ago
        page.changed_date = one_day_ago
        sitemap = CMSSitemap()
        actual_last_modification_time = sitemap.lastmod(title)
        self.assertEqual(actual_last_modification_time.date(), now.date())

    def test_templates(self):
        """
        Test the inheritance magic for templates
        """
        parent = create_page("parent", "nav_playground.html", "en")
        child = create_page("child", "nav_playground.html", "en", parent=parent)
        grand_child = create_page("grand child", "nav_playground.html", "en", parent=child)
        child2 = create_page("child2", "col_two.html", "en", parent=parent)
        grand_child2 = create_page("grand child2", "nav_playground.html", "en", parent=child2)
        child.template = constants.TEMPLATE_INHERITANCE_MAGIC
        grand_child.template = constants.TEMPLATE_INHERITANCE_MAGIC
        child.save()
        grand_child.save()
        grand_child2.template = constants.TEMPLATE_INHERITANCE_MAGIC
        grand_child2.save()

        self.assertFalse(hasattr(grand_child, '_template_cache'))
        with self.assertNumQueries(1):
            self.assertEqual(child.template, constants.TEMPLATE_INHERITANCE_MAGIC)
            self.assertEqual(parent.get_template_name(), grand_child.get_template_name())

        # test template cache
        with self.assertNumQueries(0):
            grand_child.get_template()

        self.assertFalse(hasattr(grand_child2, '_template_cache'))
        with self.assertNumQueries(1):
            self.assertEqual(child2.template, 'col_two.html')
            self.assertEqual(child2.get_template_name(), grand_child2.get_template_name())

        # test template cache
        with self.assertNumQueries(0):
            grand_child2.get_template()

        parent.template = constants.TEMPLATE_INHERITANCE_MAGIC
        parent.save()
        self.assertEqual(parent.template, constants.TEMPLATE_INHERITANCE_MAGIC)
        self.assertEqual(parent.get_template(), get_cms_setting('TEMPLATES')[0][0])
        self.assertEqual(parent.get_template_name(), get_cms_setting('TEMPLATES')[0][1])


    def test_delete_with_plugins(self):
        """
        Check that plugins and placeholders get correctly deleted when we delete
        a page!
        """
        Text = self.get_plugin_model('TextPlugin')
        home = create_page("home", "nav_playground.html", "en")
        page = create_page("page", "nav_playground.html", "en")
        page.rescan_placeholders() # create placeholders
        placeholder = page.placeholders.all()[0]
        plugin_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder,
            position=1,
            language=settings.LANGUAGES[0][0]
        )
        plugin_base = plugin_base.add_root(instance=plugin_base)

        plugin = Text(body='')
        plugin_base.set_base_attr(plugin)
        plugin.save()
        self.assertEqual(CMSPlugin.objects.count(), 1)
        self.assertEqual(Text.objects.count(), 1)
        self.assertTrue(Placeholder.objects.count() > 2)

        superuser = self.get_superuser()
        home_pl_count = home.get_placeholders().count()
        page_pl_count = page.get_placeholders().count()
        expected_pl_count = Placeholder.objects.count() - (home_pl_count + page_pl_count)

        with self.login_user_context(superuser):
            # Delete page
            self.client.post(self.get_admin_url(Page, 'delete', page.pk), {'post': 'yes'})

        with self.login_user_context(superuser):
            # Delete home page
            self.client.post(self.get_admin_url(Page, 'delete', home.pk), {'post': 'yes'})
        self.assertEqual(CMSPlugin.objects.count(), 0)
        self.assertEqual(Text.objects.count(), 0)
        self.assertEqual(Placeholder.objects.exclude(slot='clipboard').count(), expected_pl_count)
        self.assertEqual(Page.objects.count(), 0)

    def test_get_page_from_request_nopage(self):
        request = self.get_request('/')
        page = get_page_from_request(request)
        self.assertEqual(page, None)

    def test_get_page_from_request_with_page_404(self):
        page = create_page("page", "nav_playground.html", "en", published=True)
        page.publish('en')
        request = self.get_request('/does-not-exist/')
        found_page = get_page_from_request(request)
        self.assertEqual(found_page, None)

    def test_get_page_without_final_slash(self):
        root = create_page("root", "nav_playground.html", "en", slug="root",
                           published=True)
        page = create_page("page", "nav_playground.html", "en", slug="page",
                           published=True, parent=root)
        root.publish('en')
        page = page.reload()
        page.publish('en')
        request = self.get_request('/en/root/page')
        found_page = get_page_from_request(request)
        self.assertIsNotNone(found_page)
        self.assertFalse(found_page.publisher_is_draft)

    def test_ancestor_expired(self):
        yesterday = tz_now() - datetime.timedelta(days=1)
        tomorrow = tz_now() + datetime.timedelta(days=1)
        root = create_page("root", "nav_playground.html", "en", slug="root",
                           published=True)
        page_past = create_page("past", "nav_playground.html", "en", slug="past",
                                publication_end_date=yesterday,
                                published=True, parent=root)
        page_test = create_page("test", "nav_playground.html", "en", slug="test",
                                published=True, parent=page_past)
        page_future = create_page("future", "nav_playground.html", "en", slug="future",
                                  publication_date=tomorrow,
                                  published=True, parent=root)
        page_test_2 = create_page("test", "nav_playground.html", "en", slug="test",
                                  published=True, parent=page_future)

        request = self.get_request(page_test.get_absolute_url())
        page = get_page_from_request(request)
        self.assertEqual(page, None)

        request = self.get_request(page_test_2.get_absolute_url())
        page = get_page_from_request(request)
        self.assertEqual(page, None)

    def test_page_already_expired(self):
        """
        Test that a page which has a end date in the past gives a 404, not a
        500.
        """
        yesterday = tz_now() - datetime.timedelta(days=1)
        with self.settings(CMS_PERMISSION=False):
            page = create_page('page', 'nav_playground.html', 'en',
                               publication_end_date=yesterday, published=True)
            resp = self.client.get(page.get_absolute_url('en'))
            self.assertEqual(resp.status_code, 404)

    def test_page_urls(self):
        page1 = self.create_homepage('test page 1', 'nav_playground.html', 'en', published=True)

        page2 = create_page('test page 2', 'nav_playground.html', 'en',
                            published=True, parent=page1)

        page3 = create_page('test page 3', 'nav_playground.html', 'en',
                            published=True, parent=page2)

        page4 = create_page('test page 4', 'nav_playground.html', 'en',
                            published=True)

        page5 = create_page('test page 5', 'nav_playground.html', 'en',
                            published=True, parent=page4)
        page1 = page1.reload()
        page2 = page2.reload()
        page3 = page3.reload()
        page4 = page4.reload()
        page5 = page5.reload()
        self.assertEqual(page3.node.parent_id, page2.node.pk)
        self.assertEqual(page2.node.parent_id, page1.node.pk)
        self.assertEqual(page5.node.parent_id, page4.node.pk)


        self.assertEqual(page1.get_absolute_url(),
                         self.get_pages_root() + '')
        self.assertEqual(page2.get_absolute_url(),
                         self.get_pages_root() + 'test-page-2/')
        self.assertEqual(page3.get_absolute_url(),
                         self.get_pages_root() + 'test-page-2/test-page-3/')
        self.assertEqual(page4.get_absolute_url(),
                         self.get_pages_root() + 'test-page-4/')
        self.assertEqual(page5.get_absolute_url(),
                         self.get_pages_root() + 'test-page-4/test-page-5/')
        page3 = self.move_page(page3, page1)
        self.assertEqual(page3.get_absolute_url(),
                         self.get_pages_root() + 'test-page-3/')
        page3 = page3.reload()
        page2 = page2.reload()
        page5 = page5.reload()
        page5 = self.move_page(page5, page2)
        self.assertEqual(page5.get_absolute_url(),
                         self.get_pages_root() + 'test-page-2/test-page-5/')
        page3 = page3.reload()
        page4 = page4.reload()
        page3 = self.move_page(page3, page4)
        self.assertEqual(page3.get_absolute_url(),
                         self.get_pages_root() + 'test-page-4/test-page-3/')

    def test_page_and_title_repr(self):
        non_saved_page = Page()
        self.assertIsNone(non_saved_page.pk)
        self.assertIn('id=None', repr(non_saved_page))

        saved_page = create_page('test saved page', 'nav_playground.html', 'en')
        self.assertIsNotNone(saved_page.pk)
        self.assertIn('id={}'.format(saved_page.pk), repr(saved_page))
        self.assertIn('is_draft={}'.format(saved_page.publisher_is_draft), repr(saved_page))

        non_saved_title = Title()
        self.assertIsNone(non_saved_title.pk)
        self.assertIn('id=None', repr(non_saved_title))

        saved_title = saved_page.get_title_obj()
        self.assertIsNotNone(saved_title.pk)
        self.assertIn('id={}'.format(saved_title.pk), repr(saved_title))
        self.assertIn('is_draft={}'.format(saved_title.publisher_is_draft), repr(saved_title))

    def test_page_overwrite_urls(self):

        page1 = self.create_homepage('test page 1', 'nav_playground.html', 'en', published=True)

        page2 = create_page('test page 2', 'nav_playground.html', 'en',
                            published=True, parent=page1)

        page3 = create_page('test page 3', 'nav_playground.html', 'en',
                            published=True, parent=page2, overwrite_url='i-want-another-url')
        superuser = self.get_superuser()

        self.assertEqual(page2.get_absolute_url(),
                         self.get_pages_root() + 'test-page-2/')
        self.assertEqual(page3.get_absolute_url(),
                         self.get_pages_root() + 'i-want-another-url/')

        endpoint = self.get_admin_url(Page, 'change', page2.pk)

        with self.login_user_context(superuser):
            response = self.client.post(endpoint, {'title': 'test page 2', 'slug': 'page-test-2'})
            self.assertRedirects(response, self.get_admin_url(Page, 'changelist'))

        page2 = Page.objects.get(pk=page2.pk)
        page3 = Page.objects.get(pk=page3.pk)

        self.assertEqual(page2.get_absolute_url(),
                         self.get_pages_root() + 'page-test-2/')
        self.assertEqual(page3.get_absolute_url(),
                         self.get_pages_root() + 'i-want-another-url/')

        # tests a bug found in 2.2 where saving an ancestor page
        # wiped out the overwrite_url for child pages
        page2.save()
        self.assertEqual(page3.get_absolute_url(),
                         self.get_pages_root() + 'i-want-another-url/')

    def test_slug_url_overwrite_clash(self):
        """ Tests if a URL-Override clashes with a normal page url
        """
        site = get_current_site()
        with self.settings(CMS_PERMISSION=False):
            create_page('home', 'nav_playground.html', 'en', published=True)
            bar = create_page('bar', 'nav_playground.html', 'en', published=False)
            foo = create_page('foo', 'nav_playground.html', 'en', published=True)
            # Tests to assure is_valid_url is ok on plain pages
            self.assertTrue(validate_url_uniqueness(
                site,
                path=bar.get_path('en'),
                language='en',
                exclude_page=bar,
            ))
            self.assertTrue(validate_url_uniqueness(
                site,
                path=foo.get_path('en'),
                language='en',
                exclude_page=foo,
            ))

            # Set url_overwrite for page foo
            title = foo.get_title_obj(language='en')
            title.has_url_overwrite = True
            title.path = 'bar'
            title.save()
            foo.publish('en')

            self.assertRaises(
                ValidationError,
                validate_url_uniqueness,
                site,
                path=bar.get_path('en'),
                language='en',
                exclude_page=bar,
            )

    def test_valid_url_multisite(self):
        site1 = Site.objects.get_current()
        site3 = Site.objects.create(domain="sample3.com", name="sample3.com")
        home = create_page('home', 'nav_playground.html', 'de', published=True, site=site1)
        bar = create_page('bar', 'nav_playground.html', 'de', slug="bar", published=True, parent=home, site=site1)
        home_s3 = create_page('home', 'nav_playground.html', 'de', published=True, site=site3)
        bar_s3 = create_page('bar', 'nav_playground.html', 'de', slug="bar", published=True, parent=home_s3, site=site3)

        self.assertTrue(validate_url_uniqueness(
            site1,
            path=bar.get_path('de'),
            language='de',
            exclude_page=bar,
        ))

        self.assertTrue(validate_url_uniqueness(
            site3,
            path=bar_s3.get_path('de'),
            language='de',
            exclude_page=bar_s3,
        ))

    def test_home_slug_not_accessible(self):
        with self.settings(CMS_PERMISSION=False):
            page = self.create_homepage('page', 'nav_playground.html', 'en', published=True)
            self.assertEqual(page.get_absolute_url('en'), '/en/')
            resp = self.client.get('/en/')
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            resp = self.client.get('/en/page/')
            self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

    def test_plugin_loading_queries(self):
        with self.settings(
                CMS_TEMPLATES=(('placeholder_tests/base.html', 'tpl'), ),
        ):
            page = create_page('home', 'placeholder_tests/base.html', 'en', published=True, slug='home')
            placeholders = list(page.placeholders.all())
            for i, placeholder in enumerate(placeholders):
                for j in range(5):
                    add_plugin(placeholder, 'TextPlugin', 'en', body='text-%d-%d' % (i, j))
                    add_plugin(placeholder, 'LinkPlugin', 'en', name='link-%d-%d' % (i, j))

            # trigger the apphook query so that it doesn't get in our way
            reverse('pages-root')
            # trigger the get_languages query so it doesn't get in our way
            context = self.get_context(page=page)
            context['request'].current_page.get_languages()

            renderer = self.get_content_renderer(context['request'])

            with self.assertNumQueries(4):
                for i, placeholder in enumerate(placeholders):
                    content = renderer.render_page_placeholder(
                        placeholder.slot,
                        context,
                        inherit=False,
                    )
                    for j in range(5):
                        self.assertIn('text-%d-%d' % (i, j), content)
                        self.assertIn('link-%d-%d' % (i, j), content)

    def test_xframe_options_allow(self):
        """Test that no X-Frame-Options is set when page's xframe_options is set to allow"""
        page = create_page(
            title='home',
            template='nav_playground.html',
            language='en',
            published=True,
            slug='home',
            xframe_options=Page.X_FRAME_OPTIONS_ALLOW
        )

        resp = self.client.get(page.get_absolute_url('en'))
        self.assertEqual(resp.get('X-Frame-Options'), None)

    def test_xframe_options_sameorigin(self):
        """Test that X-Frame-Options is 'SAMEORIGIN' when xframe_options is set to origin"""
        page = create_page(
            title='home',
            template='nav_playground.html',
            language='en',
            published=True,
            slug='home',
            xframe_options=Page.X_FRAME_OPTIONS_SAMEORIGIN
        )

        resp = self.client.get(page.get_absolute_url('en'))
        self.assertEqual(resp.get('X-Frame-Options'), 'SAMEORIGIN')

    def test_xframe_options_deny(self):
        """Test that X-Frame-Options is 'DENY' when xframe_options is set to deny"""
        page = create_page(
            title='home',
            template='nav_playground.html',
            language='en',
            published=True,
            slug='home',
            xframe_options=Page.X_FRAME_OPTIONS_DENY
        )

        resp = self.client.get(page.get_absolute_url('en'))
        self.assertEqual(resp.get('X-Frame-Options'), 'DENY')

    def test_xframe_options_inherit_with_parent(self):
        """Test that X-Frame-Options is set to parent page's setting when inherit is set"""
        parent = create_page(
            title='home',
            template='nav_playground.html',
            language='en',
            published=True,
            slug='home',
            xframe_options=Page.X_FRAME_OPTIONS_DENY
        )

        child1 = create_page(
            title='subpage',
            template='nav_playground.html',
            language='en',
            published=True,
            slug='subpage',
            parent=parent,
            xframe_options=Page.X_FRAME_OPTIONS_INHERIT
        )

        child2 = create_page(
            title='subpage',
            template='nav_playground.html',
            language='en',
            published=True,
            slug='subpage',
            parent=child1,
            xframe_options=Page.X_FRAME_OPTIONS_ALLOW
        )
        child3 = create_page(
            title='subpage',
            template='nav_playground.html',
            language='en',
            published=True,
            slug='subpage',
            parent=child2,
            xframe_options=Page.X_FRAME_OPTIONS_INHERIT
        )

        resp = self.client.get(parent.get_absolute_url('en'))
        self.assertEqual(resp.get('X-Frame-Options'), 'DENY')

        resp = self.client.get(child1.get_absolute_url('en'))
        self.assertEqual(resp.get('X-Frame-Options'), 'DENY')

        resp = self.client.get(child2.get_absolute_url('en'))
        self.assertEqual(resp.get('X-Frame-Options'), None)

        resp = self.client.get(child3.get_absolute_url('en'))
        self.assertEqual(resp.get('X-Frame-Options'), None)

    def test_top_level_page_inherited_xframe_options_are_applied(self):
        MIDDLEWARE = settings.MIDDLEWARE + ['django.middleware.clickjacking.XFrameOptionsMiddleware']
        with self.settings(MIDDLEWARE=MIDDLEWARE):
            page = create_page('test page 1', 'nav_playground.html', 'en', published=True)
            resp = self.client.get(page.get_absolute_url('en'))
            self.assertEqual(resp.get('X-Frame-Options'), 'SAMEORIGIN')

    def test_xframe_options_with_cms_page_cache_and_clickjacking_middleware(self):
        # Refs: 6346
        override = {
            'MIDDLEWARE': settings.MIDDLEWARE + [
                'django.middleware.clickjacking.XFrameOptionsMiddleware',
            ]
        }

        override['CMS_PAGE_CACHE'] = True

        with self.settings(**override):
            page = create_page(
                'test page 1',
                'nav_playground.html',
                'en',
                published=True,
                xframe_options=Page.X_FRAME_OPTIONS_ALLOW,
            )

            # Normal response from render_page
            resp = self.client.get(page.get_absolute_url('en'))
            self.assertEqual(resp.get('X-Frame-Options'), None)

            # Response from page cache
            resp = self.client.get(page.get_absolute_url('en'))
            self.assertEqual(resp.get('X-Frame-Options'), None)

    def test_page_used_on_request(self):
        """
        The rendered page changes depending on request and
        user permissions.
        """
        superuser = self.get_superuser()
        staff_with_no_permissions = self.get_staff_user_with_no_permissions()
        draft_text = '<p>text only in draft</p>'
        public_text = '<p>text in draft &amp; live</p>'
        cms_page = create_page(
            title='home',
            template='nav_playground.html',
            language='en',
            published=True,
            slug='home',
            xframe_options=Page.X_FRAME_OPTIONS_DENY
        )
        placeholder = cms_page.placeholders.all()[0]
        add_plugin(cms_page.placeholders.all()[0], 'TextPlugin', 'en', body=public_text)
        cms_page.publish('en')
        add_plugin(placeholder, 'TextPlugin', 'en', body=draft_text)
        endpoint = cms_page.get_absolute_url('en')

        with self.login_user_context(superuser):
            # staff user with change permissions
            # draft page is always used
            resp = self.client.get(endpoint)
            self.assertContains(resp, public_text)
            self.assertContains(resp, draft_text)

        with self.login_user_context(superuser):
            # staff user with change permissions
            # draft page is used regardless of edit
            resp = self.client.get(endpoint + '?edit_off')
            self.assertContains(resp, public_text)
            self.assertContains(resp, draft_text)

        with self.login_user_context(superuser):
            # staff user with change permissions
            # draft page is used regardless of edit
            resp = self.client.get(endpoint + '?toolbar_off')
            self.assertContains(resp, public_text)
            self.assertContains(resp, draft_text)

        with self.login_user_context(superuser):
            # staff user with change permissions
            # public page is used because of explicit ?preview
            resp = self.client.get(endpoint + '?preview')
            self.assertContains(resp, public_text)
            self.assertNotContains(resp, draft_text)

        with self.login_user_context(superuser):
            # staff user with change permissions
            # public page is used because of preview disables edit
            resp = self.client.get(endpoint + '?preview&edit')
            self.assertContains(resp, public_text)
            self.assertNotContains(resp, draft_text)

        with self.login_user_context(staff_with_no_permissions):
            # staff user with no change permissions
            # public page is always used
            resp = self.client.get(endpoint)
            self.assertContains(resp, public_text)
            self.assertNotContains(resp, draft_text)

    def test_page_preview_persists(self):
        """
        Page preview persists in the user session to allow users
        to navigate the site in public mode.
        """
        superuser = self.get_superuser()
        draft_text = '<p>text only in draft</p>'
        public_text = '<p>text in draft &amp; live</p>'
        cms_page = create_page(
            title='home',
            template='nav_playground.html',
            language='en',
            published=True,
            slug='home',
            xframe_options=Page.X_FRAME_OPTIONS_DENY
        )
        placeholder = cms_page.placeholders.all()[0]
        add_plugin(cms_page.placeholders.all()[0], 'TextPlugin', 'en', body=public_text)
        cms_page.publish('en')
        add_plugin(placeholder, 'TextPlugin', 'en', body=draft_text)
        endpoint = cms_page.get_absolute_url('en')

        with self.login_user_context(superuser):
            # staff user with change permissions
            # public page is used because of explicit ?preview
            resp = self.client.get(endpoint + '?preview')
            self.assertContains(resp, public_text)
            self.assertNotContains(resp, draft_text)
            resp = self.client.get(endpoint)
            self.assertContains(resp, public_text)
            self.assertNotContains(resp, draft_text)


class PageTreeTests(CMSTestCase):

    def test_rename_node(self):
        superuser = self.get_superuser()
        home = create_page('grandpa', 'nav_playground.html', 'en', slug='home', published=True)
        home.publish('en')
        parent = create_page('parent', 'nav_playground.html', 'en', slug='parent', published=True)
        parent.publish('en')
        child = create_page('child', 'nav_playground.html', 'en', slug='child', published=True, parent=parent)
        child.publish('en')

        endpoint = self.get_admin_url(Page, 'change', parent.pk)

        with self.login_user_context(superuser):
            response = self.client.post(endpoint, {'title': 'parent', 'slug': 'father'})
            self.assertRedirects(response, self.get_admin_url(Page, 'changelist'))

        parent = Page.objects.get(pk=parent.pk)
        parent.publish('en')
        child = Page.objects.get(pk=child.pk)

        self.assertEqual(child.get_absolute_url(language='en'), '/en/father/child/')
        self.assertEqual(child.publisher_public.get_absolute_url(language='en'), '/en/father/child/')

    def test_rename_node_alters_descendants(self):
        superuser = self.get_superuser()
        create_page('grandpa', 'nav_playground.html', 'en', slug='home', published=True)
        parent = create_page('parent', 'nav_playground.html', 'en', slug='parent', published=True)
        child = create_page('child', 'nav_playground.html', 'en', slug='child', published=True, parent=parent)
        grandchild_1 = create_page('grandchild-1', 'nav_playground.html', 'en', slug='grandchild-1', published=True,
                                 parent=child)
        grandchild_2 = create_page('grandchild-2', 'nav_playground.html', 'en', slug='grandchild-2', published=True,
                                 parent=child.reload())
        grandchild_3 = create_page('grandchild-3', 'nav_playground.html', 'en', slug='grandchild-3', published=True,
                                 parent=child.reload())

        endpoint = self.get_admin_url(Page, 'change', parent.pk)

        with self.login_user_context(superuser):
            response = self.client.post(endpoint, {'title': 'parent', 'slug': 'father'})
            self.assertRedirects(response, self.get_admin_url(Page, 'changelist'))

        # Draft pages
        self.assertEqual(grandchild_1.get_absolute_url(language='en'), '/en/father/child/grandchild-1/')
        self.assertEqual(grandchild_2.get_absolute_url(language='en'), '/en/father/child/grandchild-2/')
        self.assertEqual(grandchild_3.get_absolute_url(language='en'), '/en/father/child/grandchild-3/')

        parent.reload().publish('en')

        # Public pages
        self.assertEqual(grandchild_1.publisher_public.get_absolute_url(language='en'), '/en/father/child/grandchild-1/')
        self.assertEqual(grandchild_2.publisher_public.get_absolute_url(language='en'), '/en/father/child/grandchild-2/')
        self.assertEqual(grandchild_3.publisher_public.get_absolute_url(language='en'), '/en/father/child/grandchild-3/')

    def test_move_node(self):
        home = create_page('grandpa', 'nav_playground.html', 'en', slug='home', published=True)
        home.publish('en')
        parent = create_page('parent', 'nav_playground.html', 'en', slug='parent', published=True)
        parent.publish('en')
        child = create_page('child', 'nav_playground.html', 'en', slug='child', published=True, parent=home)
        child.publish('en')

        child.move_page(parent.node)
        child = child.reload()
        child.publish('en')
        child.reload()

        self.assertEqual(child.get_absolute_url(language='en'), '/en/parent/child/')
        self.assertEqual(child.publisher_public.get_absolute_url(language='en'), '/en/parent/child/')
