# -*- coding: utf-8 -*-
import datetime
import os.path
from unittest import skipIf

from django.conf import settings
from django.core.cache import cache
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import signals
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.test.utils import override_settings
from django.utils.encoding import force_text
from django.utils.timezone import now as tz_now

from cms import constants
from cms.admin.forms import AdvancedSettingsForm
from cms.admin.pageadmin import PageAdmin
from cms.api import create_page, add_plugin, create_title, publish_page
from cms.constants import PUBLISHER_STATE_DEFAULT, PUBLISHER_STATE_DIRTY
from cms.exceptions import PublicIsUnmodifiable, PublicVersionNeeded
from cms.middleware.user import CurrentUserMiddleware
from cms.models import Page, Title, EmptyTitle
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.signals import pre_save_page, post_save_page
from cms.sitemaps import CMSSitemap
from cms.templatetags.cms_tags import get_placeholder_content
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_ADD,
                                      URL_CMS_PAGE_CHANGE, URL_CMS_PAGE_ADVANCED_CHANGE,
                                      URL_CMS_PAGE_MOVE)
from cms.test_utils.util.context_managers import LanguageOverride, UserLoginContext
from cms.utils import get_cms_setting
from cms.utils.compat.dj import installed_apps
from cms.utils.i18n import force_language
from cms.utils.page_resolver import get_page_from_request, is_valid_url
from cms.utils.page import is_valid_page_slug, get_available_slug
from cms.utils.urlutils import admin_reverse

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

    def test_add_page(self):
        """
        Test that the add admin page could be displayed via the admin
        """
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 200)

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

    def test_create_page_admin(self):
        """
        Test that a page can be created via the admin
        """
        page_data = self.get_new_page_data()

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            self.assertEqual(Title.objects.all().count(), 0)
            self.assertEqual(Page.objects.all().count(), 0)
            # crate home and auto publish
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            page_data = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)

            #self.assertEqual(Page.objects.all().count(), 2)
            #self.assertEqual(Title.objects.all().count(), 2)

            title = Title.objects.drafts().get(slug=page_data['slug'])
            self.assertRaises(Title.DoesNotExist, Title.objects.public().get, slug=page_data['slug'])

            page = title.page
            page.save()
            page.publish('en')
            self.assertEqual(page.get_title(), page_data['title'])
            self.assertEqual(page.get_slug(), page_data['slug'])
            self.assertEqual(page.placeholders.all().count(), 2)

            # were public instances created?
            self.assertEqual(Title.objects.all().count(), 4)
            title = Title.objects.drafts().get(slug=page_data['slug'])
            title = Title.objects.public().get(slug=page_data['slug'])

    def test_create_tree_admin(self):
        """
        Test that a tree can be created via the admin
        """
        page_1 = self.get_new_page_data()

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            # create home and auto publish
            response = self.client.post(URL_CMS_PAGE_ADD, page_1)
            self.assertRedirects(response, URL_CMS_PAGE)

            title_home = Title.objects.drafts().get(slug=page_1['slug'])

            page_2 = self.get_new_page_data(parent_id=title_home.page.pk)
            page_3 = self.get_new_page_data(parent_id=title_home.page.pk)
            page_4 = self.get_new_page_data(parent_id=title_home.page.pk)

            response = self.client.post(URL_CMS_PAGE_ADD, page_2)
            self.assertRedirects(response, URL_CMS_PAGE)
            response = self.client.post(URL_CMS_PAGE_ADD, page_3)
            self.assertRedirects(response, URL_CMS_PAGE)

            title_left = Title.objects.drafts().get(slug=page_2['slug'])

            response = self.client.post(URL_CMS_PAGE_ADD + '?target=%s&amp;position=right' % title_left.page.pk, page_4)
            self.assertRedirects(response, URL_CMS_PAGE)

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

    def test_slug_collision(self):
        """
        Test a slug collision
        """
        page_data = self.get_new_page_data()
        # create first page
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)

            response = self.client.post(URL_CMS_PAGE_ADD, page_data)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.request['PATH_INFO'].endswith(URL_CMS_PAGE_ADD))
            self.assertContains(response, '<ul class="errorlist"><li>Another page with this slug already exists</li></ul>')

    def test_child_slug_collision(self):
        """
        Test a slug collision
        """
        root = create_page("home", 'nav_playground.html', "en", published=True)
        page = create_page("page", 'nav_playground.html', "en")
        subPage = create_page("subpage", 'nav_playground.html', "en", parent=page)
        create_page("child-page", 'nav_playground.html', "en", parent=root)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):

            response = self.client.get(URL_CMS_PAGE_ADD+"?target=%s&position=right&site=1" % subPage.pk)
            self.assertContains(response, 'value="%s"' % page.pk)

            # slug collision between two child pages of the same node
            page_data = self.get_new_page_data(page.pk)
            page_data['slug'] = 'subpage'
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.request['PATH_INFO'].endswith(URL_CMS_PAGE_ADD))
            self.assertContains(response, '<ul class="errorlist"><li>Another page with this slug already exists</li></ul>')

            # slug collision between page with no parent and a child page of root
            page_data = self.get_new_page_data()
            page_data['slug'] = 'child-page'
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.request['PATH_INFO'].endswith(URL_CMS_PAGE_ADD))
            self.assertContains(response, '<ul class="errorlist"><li>Another page with this slug already exists</li></ul>')

            # slug collision between two top-level pages
            page_data = self.get_new_page_data()
            page_data['slug'] = 'page'
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.request['PATH_INFO'].endswith(URL_CMS_PAGE_ADD))
            self.assertContains(response, '<ul class="errorlist"><li>Another page with this slug already exists</li></ul>')

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

    def test_edit_page(self):
        """
        Test that a page can edited via the admin
        """
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            page = Page.objects.get(title_set__slug=page_data['slug'], publisher_is_draft=True)
            response = self.client.get(URL_CMS_PAGE_CHANGE % page.id)
            self.assertEqual(response.status_code, 200)
            page_data['title'] = 'changed title'
            response = self.client.post(URL_CMS_PAGE_CHANGE % page.id, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            self.assertEqual(page.get_title(), 'changed title')

    def test_moderator_edit_page_redirect(self):
        """
        Test that a page can be edited multiple times with moderator
        """
        create_page("home", "nav_playground.html", "en", published=True)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            self.assertEqual(response.status_code, 302)
            page = Page.objects.get(title_set__slug=page_data['slug'])
            response = self.client.get(URL_CMS_PAGE_CHANGE % page.id)
            self.assertEqual(response.status_code, 200)
            page_data['overwrite_url'] = '/hello/'
            page_data['has_url_overwrite'] = True
            response = self.client.post(URL_CMS_PAGE_ADVANCED_CHANGE % page.id, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            self.assertEqual(page.get_absolute_url(), '/en/hello/')
            Title.objects.all()[0]
            page = page.reload()
            page.publish('en')
            page_data['title'] = 'new title'
            response = self.client.post(URL_CMS_PAGE_CHANGE % page.id, page_data)
            page = Page.objects.get(title_set__slug=page_data['slug'], publisher_is_draft=True)
            self.assertRedirects(response, URL_CMS_PAGE)
            self.assertEqual(page.get_title(), 'new title')

    def test_meta_description_fields_from_admin(self):
        """
        Test that description and keywords tags can be set via the admin
        """
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            page_data["meta_description"] = "I am a page"
            self.client.post(URL_CMS_PAGE_ADD, page_data)
            page = Page.objects.get(title_set__slug=page_data['slug'], publisher_is_draft=True)
            response = self.client.get(URL_CMS_PAGE_CHANGE % page.id)
            self.assertEqual(response.status_code, 200)
            page_data['meta_description'] = 'I am a duck'
            response = self.client.post(URL_CMS_PAGE_CHANGE % page.id, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            page = Page.objects.get(title_set__slug=page_data["slug"], publisher_is_draft=True)
            self.assertEqual(page.get_meta_description(), 'I am a duck')

    def test_meta_description_from_template_tags(self):
        from django import template

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            page_data["title"] = "Hello"
            page_data["meta_description"] = "I am a page"
            self.client.post(URL_CMS_PAGE_ADD, page_data)
            page = Page.objects.get(title_set__slug=page_data['slug'], publisher_is_draft=True)
            self.client.post(URL_CMS_PAGE_CHANGE % page.id, page_data)
            t = template.Template(
                "{% load cms_tags %}{% page_attribute title %} {% page_attribute meta_description %}")
            req = HttpRequest()
            page.save()
            page.publish('en')
            req.current_page = page
            req.GET = {}
            self.assertEqual(t.render(template.Context({"request": req})), "Hello I am a page")

    def test_page_obj_change_data_from_template_tags(self):
        from django import template

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            change_user = str(superuser)
            # some databases don't store microseconds, so move the start flag
            # back by 1 second
            before_change = tz_now()+datetime.timedelta(seconds=-1)
            self.client.post(URL_CMS_PAGE_ADD, page_data)
            page = Page.objects.get(
                title_set__slug=page_data['slug'],
                publisher_is_draft=True
            )
            self.client.post(URL_CMS_PAGE_CHANGE % page.id, page_data)
            t = template.Template(
                "{% load cms_tags %}{% page_attribute changed_by %} changed "
                "on {% page_attribute changed_date as page_change %}"
                "{{ page_change|date:'Y-m-d\TH:i:s' }}"
            )
            req = HttpRequest()
            page.save()
            page.publish('en')
            after_change = tz_now()
            req.current_page = page
            req.GET = {}

            actual_result = t.render(template.Context({"request": req}))
            desired_result = "{0} changed on {1}".format(
                change_user,
                actual_result[-19:]
            )
            save_time = datetime.datetime.strptime(
                actual_result[-19:],
                "%Y-%m-%dT%H:%M:%S"
            )

            self.assertEqual(actual_result, desired_result)
            # direct time comparisons are flaky, so we just check if the
            # page's changed_date is within the time range taken by this test
            self.assertLessEqual(before_change, save_time)
            self.assertLessEqual(save_time, after_change)

    def test_copy_page(self):
        """
        Test that a page can be copied via the admin
        """
        page_a = create_page("page_a", "nav_playground.html", "en", published=True)
        page_a_a = create_page("page_a_a", "nav_playground.html", "en",
                               parent=page_a, published=True, reverse_id="hello")
        create_page("page_a_a_a", "nav_playground.html", "en", parent=page_a_a, published=True)

        page_b = create_page("page_b", "nav_playground.html", "en", published=True)
        page_b_a = create_page("page_b_b", "nav_playground.html", "en",
                               parent=page_b, published=True)

        count = Page.objects.drafts().count()

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            self.copy_page(page_a, page_b_a)

        self.assertEqual(Page.objects.drafts().count() - count, 3)

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

    def test_copy_self_page(self):
        """
        Test that a page can be copied via the admin
        """
        page_a = create_page("page_a", "nav_playground.html", "en")
        page_b = create_page("page_b", "nav_playground.html", "en", parent=page_a)
        page_c = create_page("page_c", "nav_playground.html", "en", parent=page_b)
        with self.login_user_context(self.get_superuser()):
            self.copy_page(page_b, page_b)
        self.assertEqual(Page.objects.drafts().count(), 5)
        self.assertEqual(Page.objects.filter(parent=page_b).count(), 2)
        page_d = Page.objects.filter(parent=page_b)[0]
        page_e = Page.objects.get(parent=page_d)
        self.assertEqual(page_d.path, '000100010001')
        self.assertEqual(page_e.path, '0001000100010001')
        page_e.delete()
        page_d.delete()
        with self.login_user_context(self.get_superuser()):
            self.copy_page(page_b, page_c)
        self.assertEqual(Page.objects.filter(parent=page_c).count(), 1)
        self.assertEqual(Page.objects.filter(parent=page_b).count(), 1)
        Page.objects.filter(parent=page_c).delete()
        self.assertEqual(Page.objects.all().count(), 3)
        page_b = page_b.reload()
        page_c = page_c.reload()
        with self.login_user_context(self.get_superuser()):
            self.copy_page(page_b, page_c, position=0)

    def test_public_exceptions(self):
        page_a = create_page("page_a", "nav_playground.html", "en", published=True)
        page_b = create_page("page_b", "nav_playground.html", "en")
        page = page_a.publisher_public
        self.assertRaises(PublicIsUnmodifiable, page.copy_page, 3, 1)
        self.assertRaises(PublicIsUnmodifiable, page.unpublish, 'en')
        self.assertRaises(PublicIsUnmodifiable, page.revert, 'en')
        self.assertRaises(PublicIsUnmodifiable, page.publish, 'en')

        self.assertTrue(page.get_draft_object().publisher_is_draft)
        self.assertRaises(PublicVersionNeeded, page_b.revert, 'en')

    def test_get_admin_tree_title(self):
        page = create_page("page_a", "nav_playground.html", "en", published=True)
        self.assertEqual(page.get_admin_tree_title(), 'page_a')
        page.title_cache = {}
        self.assertEqual("Empty", force_text(page.get_admin_tree_title()))
        languages = {
            1: [
                {
                    'code': 'en',
                    'name': 'English',
                    'fallbacks': ['fr', 'de'],
                    'public': True,
                    'fallbacks':['fr']
                },
                {
                    'code': 'fr',
                    'name': 'French',
                    'public': True,
                    'fallbacks':['en']
                },
        ]}
        with self.settings(CMS_LANGUAGES=languages):
            with force_language('fr'):
                page.title_cache = {'en': Title(slug='test', page_title="test2", title="test2")}
                self.assertEqual('test2', force_text(page.get_admin_tree_title()))
                page.title_cache = {'en': Title(slug='test', page_title="test2")}
                self.assertEqual('test2', force_text(page.get_admin_tree_title()))
                page.title_cache = {'en': Title(slug='test', menu_title="test2")}
                self.assertEqual('test2', force_text(page.get_admin_tree_title()))
                page.title_cache = {'en': Title(slug='test2')}
                self.assertEqual('test2', force_text(page.get_admin_tree_title()))
                page.title_cache = {'en': Title(slug='test2'), 'fr': EmptyTitle('fr')}
                self.assertEqual('test2', force_text(page.get_admin_tree_title()))

    def test_language_change(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_data)
            pk = Page.objects.all()[0].pk
            response = self.client.get(URL_CMS_PAGE_CHANGE % pk, {"language": "en"})
            self.assertEqual(response.status_code, 200)
            response = self.client.get(URL_CMS_PAGE_CHANGE % pk, {"language": "de"})
            self.assertEqual(response.status_code, 200)

    def test_move_page(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_home = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_home)
            page_data1 = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_data1)
            page_data2 = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_data2)
            page_data3 = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_data3)
            home = Page.objects.all()[0]
            page1 = Page.objects.all()[2]
            page2 = Page.objects.all()[3]
            page3 = Page.objects.all()[4]

            # move pages
            response = self.client.post(URL_CMS_PAGE_MOVE % page3.pk,
                                        {"target": page2.pk, "position": "last-child"})
            self.assertEqual(response.status_code, 200)

            page3 = Page.objects.get(pk=page3.pk)
            response = self.client.post(URL_CMS_PAGE_MOVE % page2.pk,
                                        {"target": page1.pk, "position": "last-child"})
            self.assertEqual(response.status_code, 200)
            # check page2 path and url
            page2 = Page.objects.get(pk=page2.pk)
            self.assertEqual(page2.get_path(), page_data1['slug'] + "/" + page_data2['slug'])
            self.assertEqual(page2.get_absolute_url(),
                             self.get_pages_root() + page_data1['slug'] + "/" + page_data2['slug'] + "/")
            # check page3 path and url
            page3 = Page.objects.get(pk=page3.pk)
            self.assertEqual(page3.get_path(), page_data1['slug'] + "/" + page_data2['slug'] + "/" + page_data3['slug'])
            self.assertEqual(page3.get_absolute_url(),
                             self.get_pages_root() + page_data1['slug'] + "/" + page_data2['slug'] + "/" + page_data3[
                                 'slug'] + "/")

            # publish page 1 (becomes home)
            home.delete()
            page1.publish('en')
            public_page1 = page1.publisher_public
            self.assertEqual(page1.get_path(), '')
            self.assertEqual(public_page1.get_path(), '')
            # check that page2 and page3 url have changed
            page2 = Page.objects.get(pk=page2.pk)
            page2.publish('en')
            public_page2 = page2.publisher_public
            self.assertEqual(public_page2.get_absolute_url(), self.get_pages_root() + page_data2['slug'] + "/")
            page3 = Page.objects.get(pk=page3.pk)
            page3.publish('en')
            public_page3 = page3.publisher_public
            self.assertEqual(public_page3.get_absolute_url(),
                             self.get_pages_root() + page_data2['slug'] + "/" + page_data3['slug'] + "/")
            # set page2 as root and check path of 1 and 3
            response = self.client.post(URL_CMS_PAGE_MOVE % page2.pk,
                                        {"position": "0"})
            self.assertEqual(response.status_code, 200)
            page1 = Page.objects.get(pk=page1.pk)
            self.assertEqual(page1.get_path(), page_data1['slug'])
            page2 = Page.objects.get(pk=page2.pk)
            # Check that page2 is now at the root of the tree
            self.assertTrue(page2.is_home)
            self.assertEqual(page2.get_path(), '')
            page3 = Page.objects.get(pk=page3.pk)
            self.assertEqual(page3.get_path(), page_data3['slug'])

    def test_move_page_integrity(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_home = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_home)

            # Create parent page
            page_root = create_page("Parent", 'col_three.html', "en")
            page_root.publish('en')

            # Create child pages
            page_child_1 = create_page(
                "Child 1",
                template=constants.TEMPLATE_INHERITANCE_MAGIC,
                language="en",
                parent=page_root,
            )
            page_child_1.publish('en')

            page_child_2 = create_page(
                "Child 2",
                template=constants.TEMPLATE_INHERITANCE_MAGIC,
                language="en",
                parent=page_root,
            )
            page_child_2.publish('en')

            # Create two root pages that ware meant as child pages
            page_child_3 = create_page("Child 3", 'col_three.html', "en")
            page_child_4 = create_page("Child 4", 'col_three.html', "en", published=True)

            # Correct our mistake.
            # Move page_child_3 to be child of parent page
            data = {
                "id": page_child_3.pk,
                "target": page_root.pk,
                "position": "0",
            }
            response = self.client.post(
                URL_CMS_PAGE_MOVE % page_child_3.pk,
                data,
            )
            self.assertEqual(response.status_code, 200)

            # Un-publish page_child_4
            page_child_4.unpublish('en')

            # Move page_child_4 to be child of parent page
            data = {
                "id": page_child_4.pk,
                "target": page_root.pk,
                "position": "0",
            }
            response = self.client.post(
                URL_CMS_PAGE_MOVE % page_child_4.pk,
                data,
            )
            self.assertEqual(response.status_code, 200)

            page_root = page_root.reload()
            page_child_4 = page_child_4.reload()

            # Ensure move worked
            self.assertEqual(page_root.get_descendants().count(), 4)

            # Ensure page_child_3 is still unpublished
            self.assertEqual(
                page_child_3.get_publisher_state("en"),
                PUBLISHER_STATE_DIRTY
            )
            self.assertEqual(page_child_3.is_published("en"), False)

            # Ensure page_child_4 is still unpublished
            self.assertEqual(
                page_child_4.get_publisher_state("en"),
                PUBLISHER_STATE_DIRTY
            )
            self.assertEqual(page_child_4.is_published("en"), False)

            # And it's public page is still has the published state
            # but is marked as unpublished
            self.assertEqual(
                page_child_4.publisher_public.get_publisher_state("en"),
                PUBLISHER_STATE_DEFAULT
            )
            self.assertEqual(
                page_child_4.publisher_public.is_published("en"),
                False,
            )

            # Ensure child one is still published
            self.assertEqual(
                page_child_1.get_publisher_state("en"),
                PUBLISHER_STATE_DEFAULT
            )
            self.assertEqual(page_child_1.is_published("en"), True)

            # Ensure child two is still published
            self.assertEqual(
                page_child_2.get_publisher_state("en"),
                PUBLISHER_STATE_DEFAULT
            )
            self.assertEqual(page_child_2.is_published("en"), True)

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
        try:
            path = os.path.join(settings.TEMPLATE_DIRS[0], 'add_placeholder.html')
        except IndexError:
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

    def test_edit_page_other_site_and_language(self):
        """
        Test that a page can edited via the admin when your current site is
        different from the site you are editing and the language isn't available
        for the current site.
        """
        self.assertEqual(Site.objects.all().count(), 1)
        site = Site.objects.create(domain='otherlang', name='otherlang', pk=2)
        # Change site for this session
        page_data = self.get_new_page_data()
        page_data['site'] = site.pk
        page_data['title'] = 'changed title'
        self.assertEqual(site.pk, 2)
        TESTLANG = get_cms_setting('LANGUAGES')[site.pk][0]['code']
        page_data['language'] = TESTLANG
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            page = Page.objects.get(title_set__slug=page_data['slug'], publisher_is_draft=True)
            with LanguageOverride(TESTLANG):
                self.assertEqual(page.get_title(), 'changed title')

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

    def test_get_page_from_request_on_non_cms_admin(self):
        request = self.get_request(
            admin_reverse('sampleapp_category_change', args=(1,))
        )
        page = get_page_from_request(request)
        self.assertEqual(page, None)

    def test_get_page_from_request_on_cms_admin(self):
        page = create_page("page", "nav_playground.html", "en")
        request = self.get_request(
            admin_reverse('cms_page_change', args=(page.pk,))
        )
        found_page = get_page_from_request(request)
        self.assertTrue(found_page)
        self.assertEqual(found_page.pk, page.pk)

    def test_get_page_from_request_on_cms_admin_nopage(self):
        request = self.get_request(
            admin_reverse('cms_page_change', args=(1,))
        )
        page = get_page_from_request(request)
        self.assertEqual(page, None)

    def test_get_page_from_request_cached(self):
        mock_page = 'hello world'
        request = self.get_request(
            admin_reverse('sampleapp_category_change', args=(1,))
        )
        request._current_page_cache = mock_page
        page = get_page_from_request(request)
        self.assertEqual(page, mock_page)

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

    def test_get_page_from_request_on_cms_admin_with_editplugin(self):
        page = create_page("page", "nav_playground.html", "en")
        request = self.get_request(
            admin_reverse('cms_page_change', args=(page.pk,)) + 'edit-plugin/42/'
        )
        found_page = get_page_from_request(request)
        self.assertTrue(found_page)
        self.assertEqual(found_page.pk, page.pk)

    def test_get_page_from_request_on_cms_admin_with_editplugin_nopage(self):
        request = self.get_request(
            admin_reverse('cms_page_change', args=(1,)) + 'edit-plugin/42/'
        )
        page = get_page_from_request(request)
        self.assertEqual(page, None)

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

    def test_existing_overwrite_url(self):
        with self.settings(CMS_PERMISSION=False):
            create_page('home', 'nav_playground.html', 'en', published=True)
            create_page('boo', 'nav_playground.html', 'en', published=True)
            data = {
                'title': 'foo',
                'overwrite_url': '/boo/',
                'slug': 'foo',
                'language': 'en',
                'template': 'nav_playground.html',
                'site': 1,
            }
            form = AdvancedSettingsForm(data)
            self.assertFalse(form.is_valid())
            self.assertTrue('overwrite_url' in form.errors)

    def test_advanced_settings_form(self):
        site = Site.objects.get_current()
        page = create_page('Page 1', 'nav_playground.html', 'en')

        # First we provide fully valid conditions to make sure
        # the form is working.
        page_data = {
            'language': 'en',
            'site': site.pk,
            'template': 'col_two.html',
        }

        form = AdvancedSettingsForm(
            data=page_data,
            instance=page,
            files=None,
        )
        self.assertTrue(form.is_valid())

        # Now switch it up by adding german as the current language
        # Note that german has not been created as page translation.
        page_data['language'] = 'de'

        form = AdvancedSettingsForm(
            data=page_data,
            instance=page,
            files=None,
        )
        no_translation_error = (u"Please create the German page translation "
                                u"before editing it's advanced settings.")
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(1, len(form.errors['__all__']))
        # Make sure we get the correct error when the given language
        # is not an existing page translation.
        self.assertEqual([no_translation_error],
                         form.errors['__all__'])

        de_translation = create_title('de', title='Page 1', page=page)
        de_translation.slug = ''
        de_translation.save()

        # First make sure the title has no slug
        self.assertEqual(de_translation.slug, '')

        form = AdvancedSettingsForm(
            data=page_data,
            instance=page,
            files=None,
        )
        no_translation_error = (u"Please set the German slug before "
                                u"editing it's advanced settings.")
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(1, len(form.errors['__all__']))
        # Make sure we get the correct error when the given language
        # is not an existing page translation.
        self.assertEqual([no_translation_error],
                         form.errors['__all__'])

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
            with self.assertNumQueries(4):
                for i, placeholder in enumerate(placeholders):
                    content = get_placeholder_content(context, context['request'], page, placeholder.slot, False, None)
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
        with self.settings(MIDDLEWARE_CLASSES=settings.MIDDLEWARE_CLASSES + ['django.middleware.clickjacking.XFrameOptionsMiddleware']):
            page = create_page('test page 1', 'nav_playground.html', 'en',
                               published=True)
            resp = self.client.get(page.get_absolute_url('en'))
            self.assertEqual(resp.get('X-Frame-Options'), 'SAMEORIGIN')

class PageAdminTestBase(CMSTestCase):
    """
    The purpose of this class is to provide some basic functionality
    to test methods of the Page admin.
    """
    placeholderconf = {'body': {
        'limits': {
            'global': 2,
            'TextPlugin': 1,
        }
    }
    }

    def get_page(self, parent=None, site=None,
                 language=None, template='nav_playground.html'):
        page_data = {
            'title': 'test page %d' % self.counter,
            'slug': 'test-page-%d' % self.counter,
            'language': settings.LANGUAGES[0][0] if not language else language,
            'template': template,
            'parent': parent if parent else None,
            'site': site if site else Site.objects.get_current(),
        }
        page_data = self.get_new_page_data_dbfields()
        return create_page(**page_data)

    def get_admin(self):
        """
        Returns a PageAdmin instance.
        """
        return PageAdmin(Page, admin.site)

    def get_post_request(self, data):
        return self.get_request(post_data=data)


class PageAdminTest(PageAdminTestBase):
    def test_form_url_page_change(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            pageadmin = self.get_admin()
            page = self.get_page()
            form_url = admin_reverse("cms_page_change", args=(page.pk,))
            # Middleware is needed to correctly setup the environment for the admin
            middleware = CurrentUserMiddleware()
            request = self.get_request()
            middleware.process_request(request)
            response = pageadmin.change_view(
                request, str(page.pk),
                form_url=form_url)
            self.assertTrue('form_url' in response.context_data)
            self.assertEqual(response.context_data['form_url'], form_url)

    def test_global_limit_on_plugin_move(self):
        admin = self.get_admin()
        superuser = self.get_superuser()
        cms_page = self.get_page()
        source_placeholder = cms_page.placeholders.get(slot='right-column')
        target_placeholder = cms_page.placeholders.get(slot='body')
        data = {
            'placeholder': source_placeholder,
            'plugin_type': 'LinkPlugin',
            'language': 'en',
        }
        plugin_1 = add_plugin(**data)
        plugin_2 = add_plugin(**data)
        plugin_3 = add_plugin(**data)
        with UserLoginContext(self, superuser):
            with self.settings(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request(
                    {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_1.pk, 'plugin_parent': ''})
                response = admin.move_plugin(request) # first
                self.assertEqual(response.status_code, 200)
                request = self.get_post_request(
                    {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_2.pk, 'plugin_parent': ''})
                response = admin.move_plugin(request) # second
                self.assertEqual(response.status_code, 200)
                request = self.get_post_request(
                    {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_3.pk, 'plugin_parent': ''})
                response = admin.move_plugin(request) # third
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content, b"This placeholder already has the maximum number of plugins (2).")

    def test_type_limit_on_plugin_move(self):
        admin = self.get_admin()
        superuser = self.get_superuser()
        cms_page = self.get_page()
        source_placeholder = cms_page.placeholders.get(slot='right-column')
        target_placeholder = cms_page.placeholders.get(slot='body')
        data = {
            'placeholder': source_placeholder,
            'plugin_type': 'TextPlugin',
            'language': 'en',
        }
        plugin_1 = add_plugin(**data)
        plugin_2 = add_plugin(**data)
        with UserLoginContext(self, superuser):
            with self.settings(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request(
                    {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_1.pk, 'plugin_parent': ''})
                response = admin.move_plugin(request) # first
                self.assertEqual(response.status_code, 200)
                request = self.get_post_request(
                    {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_2.pk, 'plugin_parent': ''})
                response = admin.move_plugin(request) # second
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content,
                                 b"This placeholder already has the maximum number (1) of allowed Text plugins.")


@override_settings(ROOT_URLCONF='cms.test_utils.project.noadmin_urls')
class NoAdminPageTests(CMSTestCase):

    def test_get_page_from_request_fakeadmin_nopage(self):
        noadmin_apps = [app for app in installed_apps() if app != 'django.contrib.admin']
        with self.settings(INSTALLED_APPS=noadmin_apps):
            request = self.get_request('/en/admin/')
            page = get_page_from_request(request)
            self.assertEqual(page, None)


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
