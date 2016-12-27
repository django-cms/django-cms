# -*- coding: utf-8 -*-
import datetime
import os.path
from unittest import skipIf

from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import signals
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.timezone import now as tz_now

from cms import constants
from cms.api import create_page, add_plugin, create_title, publish_page
from cms.constants import PUBLISHER_STATE_DEFAULT, PUBLISHER_STATE_DIRTY, PUBLISHER_STATE_PENDING
from cms.exceptions import PublicIsUnmodifiable, PublicVersionNeeded
from cms.models import Page, Title
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.signals import pre_save_page, post_save_page
from cms.sitemaps import CMSSitemap
from cms.test_utils.testcases import CMSTestCase
from cms.utils import get_cms_setting
from cms.utils.i18n import force_language
from cms.utils.page_resolver import get_page_from_request, is_valid_url
from cms.utils.page import is_valid_page_slug, get_available_slug

from djangocms_link.cms_plugins import LinkPlugin
from djangocms_text_ckeditor.cms_plugins import TextPlugin
from djangocms_text_ckeditor.models import Text


class PageMigrationTestCase(CMSTestCase):

    def test_content_type(self):
        """
        Test correct content type is set for Page object
        """
        from django.contrib.contenttypes.models import ContentType
        self.assertEqual(ContentType.objects.filter(model='page', app_label='cms').count(), 1)


def has_no_custom_user():
    return get_user_model().USERNAME_FIELD != 'email'


class PagesTestCase(CMSTestCase):

    def tearDown(self):
        cache.clear()

    def test_absolute_url(self):
        user = self.get_superuser()
        page = create_page("page", "nav_playground.html", "en", published=True)
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

    def test_treebeard_delete(self):
        """
        This is a test for #4102

        When deleting a page, parent must be updated too, to reflect the new tree status.
        This is handled by MP_NodeQuerySet (which was not used before the fix)

        """
        page1 = create_page('home', 'nav_playground.html', 'en')
        page2 = create_page('page2', 'nav_playground.html', 'en', parent=page1)
        page3 = create_page('page3', 'nav_playground.html', 'en', parent=page2)
        page1.publish('en')
        page2.publish('en')
        page3.publish('en')
        page1 = page1.reload().get_draft_object()
        page2 = page2.reload().get_draft_object()
        page3 = page3.reload().get_draft_object()

        self.assertEqual(page1.depth, 1)
        self.assertEqual(page1.numchild, 1)
        self.assertFalse(page1.is_leaf())

        self.assertEqual(page2.depth, 2)
        self.assertEqual(page2.numchild, 1)
        self.assertFalse(page2.is_leaf())

        self.assertEqual(page3.depth, 3)
        self.assertEqual(page3.numchild, 0)
        self.assertTrue(page3.is_leaf())

        page3.delete()
        page1 = page1.reload().get_draft_object()
        page2 = page2.reload().get_draft_object()

        self.assertEqual(page2.depth, 2)
        self.assertEqual(page2.numchild, 0)
        self.assertTrue(page2.is_leaf())

        page3 = create_page('page3', 'nav_playground.html', 'en', parent=page2, reverse_id='page3')
        page1 = page1.reload().get_draft_object()
        page2 = page2.reload().get_draft_object()
        page3 = page3.reload().get_draft_object()

        self.assertEqual(page2.depth, 2)
        self.assertEqual(page2.numchild, 1)
        self.assertFalse(page2.is_leaf())

        self.assertEqual(page3.depth, 3)
        self.assertEqual(page3.numchild, 0)
        self.assertTrue(page3.is_leaf())

        page1.publish('en')
        page1 = page1.reload().get_draft_object()
        page2 = page2.reload().get_draft_object()
        page3 = page3.reload().get_draft_object()

        page2.publish('en')
        page1 = page1.reload().get_draft_object()
        page2 = page2.reload().get_draft_object()
        page3 = page3.reload().get_draft_object()

        page3.publish('en')
        page1 = page1.reload().get_draft_object()
        page2 = page2.reload().get_draft_object()
        page3 = page3.reload().get_draft_object()
        page1_p = page1.reload().get_public_object()
        page2_p = page2.reload().get_public_object()
        page3_p = page3.reload().get_public_object()

        self.assertEqual(page1.depth, 1)
        self.assertEqual(page1.numchild, 1)
        self.assertFalse(page1.is_leaf())

        self.assertEqual(page2.depth, 2)
        self.assertEqual(page2.numchild, 1)
        self.assertFalse(page2.is_leaf())

        self.assertEqual(page3.depth, 3)
        self.assertEqual(page3.numchild, 0)
        self.assertTrue(page3.is_leaf())

        self.assertEqual(page1_p.depth, 1)
        self.assertEqual(page1_p.numchild, 1)
        self.assertFalse(page1_p.is_leaf())

        self.assertEqual(page2_p.depth, 2)
        self.assertEqual(page2_p.numchild, 1)
        self.assertFalse(page2_p.is_leaf())

        self.assertEqual(page3_p.depth, 3)
        self.assertEqual(page3_p.numchild, 0)
        self.assertTrue(page3_p.is_leaf())

    def test_create_page_api(self):
        page_data = {
            'title': 'root',
            'slug': 'root',
            'language': settings.LANGUAGES[0][0],
            'template': 'nav_playground.html',

        }
        page = create_page(**page_data)
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

        self.assertEqual(list(Title.objects.drafts().values_list('path', flat=True)), [u''])

    def test_delete_page_no_template(self):
        page_data = {
            'title': 'root',
            'slug': 'root',
            'language': settings.LANGUAGES[0][0],
            'template': 'nav_playground.html',

        }
        page = create_page(**page_data)
        page.template = 'no_such_template.html'
        signals.pre_save.disconnect(pre_save_page, sender=Page, dispatch_uid='cms_pre_save_page')
        signals.post_save.disconnect(post_save_page, sender=Page, dispatch_uid='cms_post_save_page')
        page.save(no_signals=True)
        signals.pre_save.connect(pre_save_page, sender=Page, dispatch_uid='cms_pre_save_page')
        signals.post_save.connect(post_save_page, sender=Page, dispatch_uid='cms_post_save_page')
        page.delete()

        self.assertEqual(Page.objects.count(), 0)

    def test_get_available_slug_recursion(self):
        """ Checks cms.utils.page.get_available_slug for infinite recursion
        """
        for x in range(0, 12):
            page1 = create_page('test copy', 'nav_playground.html', 'en',
                                published=True)
        new_slug = get_available_slug(page1.get_title_obj('en'), 'test-copy')
        self.assertTrue(new_slug, 'test-copy-11')

    def test_slug_collisions_api_1(self):
        """ Checks for slug collisions on sibling pages - uses API to create pages
        """
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)
        page1_1 = create_page('test page 1_1', 'nav_playground.html', 'en',
                              published=True, parent=page1, slug="foo")
        page1_2 = create_page('test page 1_2', 'nav_playground.html', 'en',
                              published=True, parent=page1, slug="foo")
        # both sibling pages has same slug, so both pages has an invalid slug
        self.assertFalse(is_valid_page_slug(page1_1, page1_1.parent, "en", page1_1.get_slug("en"), page1_1.site))
        self.assertFalse(is_valid_page_slug(page1_2, page1_2.parent, "en", page1_2.get_slug("en"), page1_2.site))

    def test_slug_collisions_api_2(self):
        """ Checks for slug collisions on root (not home) page and a home page child - uses API to create pages
        """
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)
        page1_1 = create_page('test page 1_1', 'nav_playground.html', 'en',
                              published=True, parent=page1, slug="foo")
        page2 = create_page('test page 1_1', 'nav_playground.html', 'en',
                            published=True, slug="foo")
        # Root (non home) page and child page has the same slug, both are invalid
        self.assertFalse(is_valid_page_slug(page1_1, page1_1.parent, "en", page1_1.get_slug("en"), page1_1.site))
        self.assertFalse(is_valid_page_slug(page2, page2.parent, "en", page2.get_slug("en"), page2.site))

    def test_slug_collisions_api_3(self):
        """ Checks for slug collisions on children of a non root page - uses API to create pages
        """
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
        self.assertTrue(is_valid_page_slug(page1_1, page1_1.parent, "en", page1_1.get_slug("en"), page1_1.site))
        self.assertTrue(is_valid_page_slug(page1_2, page1_2.parent, "en", page1_2.get_slug("en"), page1_2.site))
        # children of page1_1 has the same slug -> you lose!
        self.assertFalse(
            is_valid_page_slug(page1_1_1, page1_1_1.parent, "en", page1_1_1.get_slug("en"), page1_1_1.site))
        self.assertFalse(
            is_valid_page_slug(page1_1_2, page1_1_2.parent, "en", page1_1_2.get_slug("en"), page1_1_2.site))

    def test_details_view(self):
        """
        Test the details view
        """
        superuser = self.get_superuser()
        self.assertEqual(Page.objects.all().count(), 0)
        with self.login_user_context(superuser):
            response = self.client.get(self.get_pages_root())
            self.assertEqual(response.status_code, 404)
            page = create_page('test page 1', "nav_playground.html", "en")
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

    def test_copy_page_method(self):
        """
        Test that a page can be copied via the admin
        """
        page_a = create_page("page_a", "nav_playground.html", "en", published=False)
        page_a_a = create_page("page_a_a", "nav_playground.html", "en",
                               parent=page_a, published=False, reverse_id="hello")
        create_page("page_a_a_a", "nav_playground.html", "en", parent=page_a_a, published=False)
        site = Site.objects.create(domain='whatever.com', name='whatever')

        pages = Page.objects.drafts().filter(site_id=1, depth=1)
        with transaction.atomic():
            for page in pages:
                page.copy_page(None, site)

        with transaction.atomic():
            for page in pages:
                page.copy_page(None, site)

        self.assertEqual(Page.objects.filter(site_id=1, depth=1).count(), 1)
        self.assertEqual(Page.objects.filter(site_id=1).count(), 3)
        self.assertEqual(Page.objects.filter(site_id=site.pk, depth=1).count(), 2)
        self.assertEqual(Page.objects.filter(site_id=site.pk).count(), 6)

    def test_public_exceptions(self):
        page_a = create_page("page_a", "nav_playground.html", "en", published=True)
        page_b = create_page("page_b", "nav_playground.html", "en")
        page = page_a.publisher_public
        self.assertRaises(PublicIsUnmodifiable, page.copy_page, 3, 1)
        self.assertRaises(PublicIsUnmodifiable, page.unpublish, 'en')
        self.assertRaises(PublicIsUnmodifiable, page.reset_to_public, 'en')
        self.assertRaises(PublicIsUnmodifiable, page.publish, 'en')

        self.assertTrue(page.get_draft_object().publisher_is_draft)
        self.assertRaises(PublicVersionNeeded, page_b.reset_to_public, 'en')

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
        beta.move_page(alpha, position='left')

        alpha.refresh_from_db()
        beta.refresh_from_db()

        # Draft
        self.assertEqual(home.path, '0001')
        self.assertEqual(beta.path, '00010001')
        self.assertEqual(alpha.path, '00010002')

        # Public
        self.assertEqual(home.publisher_public.path, '0002')
        self.assertEqual(beta.publisher_public.path, '00020001')
        self.assertEqual(alpha.publisher_public.path, '00020002')

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
        beta.move_page(alpha, position='left')

        alpha.refresh_from_db()
        beta.refresh_from_db()

        # Draft
        self.assertEqual(home.path, '0001')
        self.assertEqual(beta.path, '00010001')
        self.assertEqual(alpha.path, '00010002')

        # Public
        self.assertEqual(home.publisher_public.path, '0002')
        self.assertEqual(beta.publisher_public.path, '00020001')
        self.assertEqual(alpha.publisher_public.path, '00020002')

    def test_move_page_regression_5640(self):
        # ref: https://github.com/divio/django-cms/issues/5640
        alpha = create_page("Alpha", "nav_playground.html", "en", published=True)
        beta = create_page("Beta", "nav_playground.html", "en", published=False)
        alpha.move_page(beta, position='right')
        alpha = alpha.reload()
        beta = beta.reload()

        self.assertEqual(beta.path, '0003')
        # Draft
        self.assertEqual(alpha.path, '0004')
        # Public
        self.assertEqual(alpha.publisher_public.path, '0005')

    def test_move_page_regression_nested_5640(self):
        # ref: https://github.com/divio/django-cms/issues/5640
        alpha = create_page("Alpha", "nav_playground.html", "en", published=True)
        beta = create_page("Beta", "nav_playground.html", "en", published=False)
        gamma = create_page("Gamma", "nav_playground.html", "en", published=False)
        delta = create_page("Delta", "nav_playground.html", "en", published=True)
        theta = create_page("Theta", "nav_playground.html", "en", published=True)

        beta.move_page(alpha, position='last-child')
        gamma.move_page(beta.reload(), position='last-child')
        delta.move_page(gamma.reload(), position='last-child')
        theta.move_page(delta.reload(), position='last-child')

        alpha = alpha.reload()
        beta = beta.reload()
        gamma = gamma.reload()
        delta = delta.reload()
        theta = theta.reload()

        tree = [
            (alpha, '0001'),
            (beta, '00010001'),
            (gamma, '000100010001'),
            (delta, '0001000100010001'),
            (theta, '00010001000100010001'),
            (alpha.publisher_public, '0002'),
            (delta.publisher_public, '0006'),
            (theta.publisher_public, '00060001'),
        ]

        for page, path in tree:
            self.assertEqual(page.path, path)

    def test_move_page_regression_5643(self):
        # ref: https://github.com/divio/django-cms/issues/5643
        alpha = create_page("Alpha", "nav_playground.html", "en", published=True)
        beta = create_page("Beta", "nav_playground.html", "en", published=False)
        gamma = create_page("Gamma", "nav_playground.html", "en", published=False)
        delta = create_page("Delta", "nav_playground.html", "en", published=True)
        theta = create_page("Theta", "nav_playground.html", "en", published=True)

        beta.move_page(alpha, position='last-child')
        gamma.move_page(beta.reload(), position='last-child')
        delta.move_page(gamma.reload(), position='last-child')
        theta.move_page(delta.reload(), position='last-child')

        tree = [
            (alpha, PUBLISHER_STATE_DEFAULT),
            (beta, PUBLISHER_STATE_DIRTY),
            (gamma, PUBLISHER_STATE_DIRTY),
            (delta, PUBLISHER_STATE_PENDING),
            (theta, PUBLISHER_STATE_PENDING),
        ]

        for page, state in tree:
            self.assertEqual(page.get_publisher_state('en'), state)

    def test_publish_page_regression_5642(self):
        # ref: https://github.com/divio/django-cms/issues/5642
        alpha = create_page("Alpha", "nav_playground.html", "en", published=True)
        beta = create_page("Beta", "nav_playground.html", "en", published=False)
        gamma = create_page("Gamma", "nav_playground.html", "en", published=False)
        delta = create_page("Delta", "nav_playground.html", "en", published=True)
        theta = create_page("Theta", "nav_playground.html", "en", published=True)

        beta.move_page(alpha, position='last-child')
        gamma.move_page(beta.reload(), position='last-child')
        delta.move_page(gamma.reload(), position='last-child')
        theta.move_page(delta.reload(), position='last-child')

        beta.publish('en')

        # The delta and theta pages should remain pending publication
        # because gamma is still unpublished

        self.assertTrue(beta.is_published('en'))
        self.assertEqual(beta.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

        self.assertFalse(gamma.is_published('en'))
        self.assertEqual(gamma.get_publisher_state('en'), PUBLISHER_STATE_DIRTY)

        self.assertTrue(delta.is_published('en'))
        self.assertEqual(delta.get_publisher_state('en'), PUBLISHER_STATE_PENDING)

        self.assertTrue(theta.is_published('en'))
        self.assertEqual(theta.get_publisher_state('en'), PUBLISHER_STATE_PENDING)

        gamma.publish('en')

        gamma = gamma.reload()
        delta = delta.reload()
        theta = theta.reload()

        self.assertTrue(gamma.is_published('en'))
        self.assertEqual(gamma.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

        self.assertTrue(delta.is_published('en'))
        self.assertEqual(delta.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

        self.assertTrue(theta.is_published('en'))
        self.assertEqual(theta.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

    def test_move_page_inherit(self):
        parent = create_page("Parent", 'col_three.html', "en")
        child = create_page("Child", constants.TEMPLATE_INHERITANCE_MAGIC,
                            "en", parent=parent)
        self.assertEqual(child.get_template(), parent.get_template())
        child.move_page(parent, 'left')
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

        # kill template cache
        delattr(grand_child, '_template_cache')
        with self.assertNumQueries(1):
            self.assertEqual(child.template, constants.TEMPLATE_INHERITANCE_MAGIC)
            self.assertEqual(parent.get_template_name(), grand_child.get_template_name())

        # test template cache
        with self.assertNumQueries(0):
            grand_child.get_template()

        # kill template cache
        delattr(grand_child2, '_template_cache')
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
        page.delete()
        home.delete()
        self.assertEqual(CMSPlugin.objects.count(), 0)
        self.assertEqual(Text.objects.count(), 0)
        self.assertEqual(Placeholder.objects.count(), 0)
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
        request = self.get_request('/en/page')
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
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)

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
        self.assertEqual(page3.parent_id, page2.pk)
        self.assertEqual(page2.parent_id, page1.pk)
        self.assertEqual(page5.parent_id, page4.pk)


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
        self.assertEqual(len(page3.path), len(page3.publisher_public.path))
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

    def test_page_overwrite_urls(self):
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
                            published=True)

        page2 = create_page('test page 2', 'nav_playground.html', 'en',
                            published=True, parent=page1)

        page3 = create_page('test page 3', 'nav_playground.html', 'en',
                            published=True, parent=page2, overwrite_url='i-want-another-url')

        self.assertEqual(page2.get_absolute_url(),
                         self.get_pages_root() + 'test-page-2/')
        self.assertEqual(page3.get_absolute_url(),
                         self.get_pages_root() + 'i-want-another-url/')

        title2 = page2.title_set.get()
        title2.slug = 'page-test-2'
        title2.save()

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
        with self.settings(CMS_PERMISSION=False):
            create_page('home', 'nav_playground.html', 'en', published=True)
            bar = create_page('bar', 'nav_playground.html', 'en', published=False)
            foo = create_page('foo', 'nav_playground.html', 'en', published=True)
            # Tests to assure is_valid_url is ok on plain pages
            self.assertTrue(is_valid_url(bar.get_absolute_url('en'), bar))
            self.assertTrue(is_valid_url(foo.get_absolute_url('en'), foo))

            # Set url_overwrite for page foo
            title = foo.get_title_obj(language='en')
            title.has_url_overwrite = True
            title.path = '/bar/'
            title.save()
            foo.publish('en')

            try:
                url = is_valid_url(bar.get_absolute_url('en'), bar)
            except ValidationError:
                url = False
            if url:
                bar.save()
                bar.publish('en')
            self.assertFalse(bar.is_published('en'))

    def test_valid_url_multisite(self):
        site1 = Site.objects.get_current()
        site3 = Site.objects.create(domain="sample3.com", name="sample3.com")
        home = create_page('home', 'nav_playground.html', 'de', published=True, site=site1)
        bar = create_page('bar', 'nav_playground.html', 'de', slug="bar", published=True, parent=home, site=site1)
        home_s3 = create_page('home', 'nav_playground.html', 'de', published=True, site=site3)
        bar_s3 = create_page('bar', 'nav_playground.html', 'de', slug="bar", published=True, parent=home_s3, site=site3)

        self.assertTrue(is_valid_url(bar.get_absolute_url('de'), bar))
        self.assertTrue(is_valid_url(bar_s3.get_absolute_url('de'), bar_s3))

    def test_home_slug_not_accessible(self):
        with self.settings(CMS_PERMISSION=False):
            page = create_page('page', 'nav_playground.html', 'en', published=True)
            self.assertEqual(page.get_absolute_url('en'), '/en/')
            resp = self.client.get('/en/')
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            resp = self.client.get('/en/page/')
            self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

    def test_public_home_page_replaced(self):
        """Test that publishing changes to the home page doesn't move the public version"""
        home = create_page('home', 'nav_playground.html', 'en', published=True, slug='home')
        self.assertEqual(Page.objects.drafts().get_home().get_slug(), 'home')
        home.publish('en')
        self.assertEqual(Page.objects.public().get_home().get_slug(), 'home')
        other = create_page('other', 'nav_playground.html', 'en', published=True, slug='other')
        other.publish('en')
        self.assertEqual(Page.objects.drafts().get_home(), home)
        self.assertEqual(Page.objects.drafts().get_home().get_slug(), 'home')
        self.assertEqual(Page.objects.public().get_home().get_slug(), 'home')
        home = Page.objects.get(pk=home.id)
        home.in_navigation = True
        home.save()
        home.publish('en')
        self.assertEqual(Page.objects.drafts().get_home().get_slug(), 'home')
        self.assertEqual(Page.objects.public().get_home().get_slug(), 'home')

    def test_plugin_loading_queries(self):
        with self.settings(
                CMS_TEMPLATES=(('placeholder_tests/base.html', 'tpl'), ),
        ):
            page = create_page('home', 'placeholder_tests/base.html', 'en', published=True, slug='home')
            placeholders = list(page.placeholders.all())
            for i, placeholder in enumerate(placeholders):
                for j in range(5):
                    add_plugin(placeholder, TextPlugin, 'en', body='text-%d-%d' % (i, j))
                    add_plugin(placeholder, LinkPlugin, 'en', name='link-%d-%d' % (i, j))

            # trigger the apphook query so that it doesn't get in our way
            reverse('pages-root')
            # trigger the get_languages query so it doesn't get in our way
            context = self.get_context(page=page)
            context['request'].current_page.get_languages()

            content_renderer = context['cms_content_renderer']
            with self.assertNumQueries(4):
                for i, placeholder in enumerate(placeholders):
                    content = content_renderer.render_page_placeholder(
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
        if getattr(settings, 'MIDDLEWARE', None):
            override = {
                'MIDDLEWARE': settings.MIDDLEWARE + [
                    'django.middleware.clickjacking.XFrameOptionsMiddleware']
            }
        else:
            override = {
                'MIDDLEWARE_CLASSES': settings.MIDDLEWARE_CLASSES + [
                    'django.middleware.clickjacking.XFrameOptionsMiddleware']
            }
        with self.settings(**override):
            page = create_page('test page 1', 'nav_playground.html', 'en', published=True)
            resp = self.client.get(page.get_absolute_url('en'))
            self.assertEqual(resp.get('X-Frame-Options'), 'SAMEORIGIN')


class PreviousFilteredSiblingsTests(CMSTestCase):

    def test_with_publisher(self):
        home = create_page('home', 'nav_playground.html', 'en', published=True)
        home.publish('en')
        other = create_page('other', 'nav_playground.html', 'en', published=True)
        other.publish('en')
        other = Page.objects.get(pk=other.pk)
        home = Page.objects.get(pk=home.pk)
        self.assertEqual(other.get_previous_filtered_sibling(), home)
        self.assertEqual(home.get_previous_filtered_sibling(), None)

    def test_multisite(self):
        firstsite = Site.objects.create(name='first', domain='first.com')
        secondsite = Site.objects.create(name='second', domain='second.com')
        home = create_page('home', 'nav_playground.html', 'de', site=firstsite)
        home.publish('de')
        other = create_page('other', 'nav_playground.html', 'de', site=secondsite)
        other.publish('de')
        other = Page.objects.get(pk=other.pk)
        home = Page.objects.get(pk=home.pk)
        self.assertEqual(other.get_previous_filtered_sibling(), None)
        self.assertEqual(home.get_previous_filtered_sibling(), None)


class PageTreeTests(CMSTestCase):

    def test_rename_node(self):
        home = create_page('grandpa', 'nav_playground.html', 'en', slug='home', published=True)
        home.publish('en')
        parent = create_page('parent', 'nav_playground.html', 'en', slug='parent', published=True)
        parent.publish('en')
        child = create_page('child', 'nav_playground.html', 'en', slug='child', published=True, parent=parent)
        child.publish('en')

        page_title = Title.objects.get(page=parent)
        page_title.slug = "father"
        page_title.save()

        parent = Page.objects.get(pk=parent.pk)
        parent.publish('en')
        child = Page.objects.get(pk=child.pk)

        self.assertEqual(child.get_absolute_url(language='en'), '/en/father/child/')
        self.assertEqual(child.publisher_public.get_absolute_url(language='en'), '/en/father/child/')


    def test_move_node(self):
        home = create_page('grandpa', 'nav_playground.html', 'en', slug='home', published=True)
        home.publish('en')
        parent = create_page('parent', 'nav_playground.html', 'en', slug='parent', published=True)
        parent.publish('en')
        child = create_page('child', 'nav_playground.html', 'en', slug='child', published=True, parent=home)
        child.publish('en')

        child.move_page(parent)
        child = child.reload()
        child.publish('en')
        child.reload()

        self.assertEqual(child.get_absolute_url(language='en'), '/en/parent/child/')
        self.assertEqual(child.publisher_public.get_absolute_url(language='en'), '/en/parent/child/')
