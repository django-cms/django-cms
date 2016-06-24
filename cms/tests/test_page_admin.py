# -*- coding: utf-8 -*-
import datetime

from django.core.cache import cache
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, AnonymousUser
from django.contrib.admin.sites import site, AdminSite
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.utils.http import urlencode
from django.test.utils import override_settings
from django.utils.encoding import force_text
from django.utils.timezone import now as tz_now

from cms import constants
from cms.admin.forms import AdvancedSettingsForm
from cms.admin.pageadmin import PageAdmin
from cms.admin.permissionadmin import PagePermissionInlineAdmin
from cms.api import assign_user_to_page, create_page, add_plugin, create_title
from cms.constants import PUBLISHER_STATE_DEFAULT, PUBLISHER_STATE_DIRTY
from cms.middleware.user import CurrentUserMiddleware
from cms.models.pagemodel import Page
from cms.models.permissionmodels import GlobalPagePermission, PagePermission
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import EmptyTitle, Title
from cms.test_utils.testcases import (
    CMSTestCase, URL_CMS_PAGE_DELETE, URL_CMS_PAGE, URL_CMS_PAGE_MOVE,
    URL_CMS_PAGE_ADVANCED_CHANGE, URL_CMS_TRANSLATION_DELETE,
    URL_CMS_PAGE_CHANGE_LANGUAGE, URL_CMS_PAGE_CHANGE,
    URL_CMS_PAGE_PERMISSIONS, URL_CMS_PAGE_ADD, URL_CMS_PAGE_PUBLISHED,
)
from cms.test_utils.util.context_managers import LanguageOverride, UserLoginContext
from cms.utils import get_cms_setting
from cms.utils.compat.dj import installed_apps
from cms.utils.i18n import force_language
from cms.utils.page_resolver import get_page_from_request
from cms.utils.urlutils import admin_reverse

from djangocms_text_ckeditor.models import Text


class PageTestBase(CMSTestCase):
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
        page_data = self.get_new_page_data_dbfields()
        return create_page(**page_data)

    def get_admin(self):
        """
        Returns a PageAdmin instance.
        """
        return PageAdmin(Page, admin.site)

    def get_post_request(self, data):
        return self.get_request(post_data=data)


class PageTest(PageTestBase):

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
                                u"before editing its advanced settings.")
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
                                u"editing its advanced settings.")
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(1, len(form.errors['__all__']))
        # Make sure we get the correct error when the given language
        # is not an existing page translation.
        self.assertEqual([no_translation_error],
                         form.errors['__all__'])

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


class PermissionsTestCase(CMSTestCase):

    def _add_plugin_to_page(self, page, plugin_type, language='en'):
        plugin_data = {
            'TextPlugin': {'body': 'text'}
        }
        placeholder = page.placeholders.get(slot='body')
        plugin = add_plugin(placeholder, plugin_type, language, **plugin_data[plugin_type])
        page.publish('en')
        return plugin

    def _add_translation_to_page(self, page):
        translation = create_title(
            "de",
            "permissions-de",
            page.reload(),
            slug="permissions-de"
        )
        return translation

    def _page_exists(self, reverse_id=None):
        if not reverse_id:
            reverse_id = 'permissions'
        return Page.objects.filter(reverse_id=reverse_id).exists()

    def _translation_exists(self, slug=None, title=None):
        if not slug:
            slug = 'permissions-de'

        lookup = Title.objects.filter(slug=slug)

        if title:
            lookup = lookup.filter(title=title)
        return lookup.exists()

    def _get_add_plugin_uri(self, page, plugin_type, language='en'):
        endpoint = self.get_admin_url(Page, 'add_plugin')
        placeholder = page.placeholders.get(slot='body')
        uri = endpoint + '?' + urlencode({
            'plugin_type': plugin_type,
            'placeholder_id': placeholder.pk,
            'plugin_language': language,
        })
        return uri

    def get_page_dummy_data(self, permissions_inline=False, **kwargs):
        site = Site.objects.get_current()
        data = {
            'title': 'permissions',
            'slug': 'permissions',
            'language': 'en',
            'site': site.pk,
            'template': 'nav_playground.html',
        }

        if permissions_inline:
            permissions = {
                'pagepermission_set-TOTAL_FORMS': 0,
                'pagepermission_set-INITIAL_FORMS': 0,
                'pagepermission_set-MAX_NUM_FORMS': 0,
                'pagepermission_set-2-TOTAL_FORMS': 0,
                'pagepermission_set-2-INITIAL_FORMS': 0,
                'pagepermission_set-2-MAX_NUM_FORMS': 0,
            }
            data.update(permissions)
        data.update(**kwargs)
        return data


@override_settings(CMS_PERMISSION=True)
class PermissionsOnGlobalTest(PermissionsTestCase):

    def test_pages_in_admin_index(self):
        endpoint = admin_reverse('app_list', args=['cms'])
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                '<a href="/en/admin/cms/page/">Pages</a>',
                html=True,
            )

        endpoint = self.get_admin_url(Page, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)

    def test_pages_not_in_admin_index(self):
        endpoint = admin_reverse('app_list', args=['cms'])
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 404)

        endpoint = self.get_admin_url(Page, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)

    def test_user_can_edit_page_settings(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'change', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()

        data = self.get_page_dummy_data(slug='permissions-2')

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertTrue(self._translation_exists(slug='permissions-2'))

    def test_user_cant_edit_page_settings(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'change', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        data = self.get_page_dummy_data(slug='permissions-2')

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._translation_exists(slug='permissions-2'))

    def test_user_can_edit_advanced_page_settings(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'advanced', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()

        data = self.get_page_dummy_data(reverse_id='permissions-2')

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)
        self.add_global_permission(staff_user, can_change_advanced_settings=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertTrue(self._page_exists(reverse_id='permissions-2'))

    def test_user_cant_edit_advanced_page_settings(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'advanced', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        data = self.get_page_dummy_data(reverse_id='permissions-2')

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)
        self.add_global_permission(staff_user, can_change_advanced_settings=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._page_exists(reverse_id='permissions-2'))

    def test_user_can_delete_empty_page(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._page_exists())

    def test_user_cant_delete_empty_page(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_delete=False)

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

    def test_user_can_delete_non_empty_page(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()

        self._add_plugin_to_page(page, 'TextPlugin')

        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._page_exists())

    def test_user_cant_delete_non_empty_page(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        self._add_plugin_to_page(page, 'TextPlugin')

        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

    def test_user_can_delete_empty_translation(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'language': translation.language}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._translation_exists())

    def test_user_cant_delete_empty_translation(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_delete=False)

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

    def test_user_can_delete_non_empty_translation(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self._add_plugin_to_page(page, 'TextPlugin', translation.language)

        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'language': translation.language}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._translation_exists())

    def test_user_cant_delete_non_empty_translation(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self._add_plugin_to_page(page, 'TextPlugin', translation.language)

        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

    def test_user_can_view_page_permissions_summary(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'get_permissions', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        with self.login_user_context(staff_user):
            data = {'post': 'true'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                "<p>Page doesn't inherit any permissions.</p>",
                html=True,
            )

    def test_user_cant_view_page_permissions_summary(self):
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'get_permissions', page.pk)
        non_staff_user = self.get_standard_user()

        with self.login_user_context(non_staff_user):
            data = {'post': 'true'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, '/en/admin/login/?next=%s' % endpoint)

    def test_page_permission_inline_visibility(self):
        User = get_user_model()

        fields = dict(email='user@domain.com', password='user', is_staff=True)

        if get_user_model().USERNAME_FIELD != 'email':
            fields[get_user_model().USERNAME_FIELD] = 'user'

        user = User(**fields)
        user.save()
        self._give_page_permission_rights(user)
        page = create_page('A', 'nav_playground.html', 'en')
        page_permission = PagePermission.objects.create(
            can_change_permissions=True, user=user, page=page)
        request = self._get_change_page_request(user, page)
        page_admin = PageAdmin(Page, AdminSite())
        page_admin._current_page = page
        # user has can_change_permission
        # => must see the PagePermissionInline
        self.assertTrue(
            any(type(inline) is PagePermissionInlineAdmin
                for inline in page_admin.get_inline_instances(request, page)))

        page = Page.objects.get(pk=page.pk)
        # remove can_change_permission
        page_permission.can_change_permissions = False
        page_permission.save()
        request = self._get_change_page_request(user, page)
        page_admin = PageAdmin(Page, AdminSite())
        page_admin._current_page = page
        # => PagePermissionInline is no longer visible
        self.assertFalse(
            any(type(inline) is PagePermissionInlineAdmin
                for inline in page_admin.get_inline_instances(request, page)))

    def test_user_can_edit_title(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        title = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'edit_title_fields', page.pk, title.language)

        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = model_to_dict(title, fields=['title'])
            data['title'] = 'permissions-de-2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(self._translation_exists(title='permissions-de-2'))

    def test_user_cant_edit_title(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        title = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'edit_title_fields', page.pk, title.language)

        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = model_to_dict(title, fields=['title'])
            data['title'] = 'permissions-de-2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._translation_exists(title='permissions-de-2'))

    # Plugin related tests

    def test_user_can_add_plugin(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        endpoint = self._get_add_plugin_uri(page, 'TextPlugin')

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_text')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {})
            self.assertEqual(response.status_code, 302)

    def test_plugin_cant_add(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        endpoint = self._get_add_plugin_uri(page, 'LinkPlugin')

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {})
            print endpoint
            self.assertEqual(response.status_code, 403)

    def test_user_can_edit_plugin(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page, 'TextPlugin')
        endpoint = self.get_admin_url(Page, 'edit_plugin', plugin.pk)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_text')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['body'])
            data['text'] = 'new text'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

    def test_user_cant_edit_plugin(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page, 'TextPlugin')
        endpoint = self.get_admin_url(Page, 'edit_plugin', plugin.pk)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_text')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['body'])
            data['text'] = 'new text'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)

    def test_user_can_delete_plugin(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page, 'TextPlugin')
        endpoint = self.get_admin_url(Page, 'delete_plugin', plugin.pk)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_text')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = {'post': True}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

    def test_user_cant_delete_plugin(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page, 'TextPlugin')
        endpoint = self.get_admin_url(Page, 'delete_plugin', plugin.pk)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_text')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = {'post': True}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)

    def test_user_can_move_plugin(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page, 'TextPlugin')
        endpoint = self.get_admin_url(Page, 'move_plugin')
        placeholder = page.placeholders.get(slot='right-column')

        data = {
            'plugin_id': plugin.pk,
            'placeholder_id': placeholder.pk,
            'plugin_parent': '',
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_text')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

    def test_user_cant_move_plugin(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page, 'TextPlugin')
        endpoint = self.get_admin_url(Page, 'move_plugin')
        placeholder = page.placeholders.get(slot='right-column')

        data = {
            'plugin_id': plugin.pk,
            'placeholder_id': placeholder.pk,
            'plugin_parent': '',
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_text')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)

    def test_user_can_copy_plugin(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page, 'TextPlugin')
        translation = self._add_translation_to_page(page)
        placeholder = page.placeholders.get(slot='right-column')
        endpoint = self.get_admin_url(Page, 'copy_plugins')

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': placeholder.pk,
            'source_language': plugin.language,
            'target_language': translation.language,
            'target_placeholder_id': placeholder.pk,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_text')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

    def test_user_cant_copy_plugin(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page, 'TextPlugin')
        translation = self._add_translation_to_page(page)
        placeholder = page.placeholders.get(slot='right-column')
        endpoint = self.get_admin_url(Page, 'copy_plugins')

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': placeholder.pk,
            'source_language': plugin.language,
            'target_language': translation.language,
            'target_placeholder_id': placeholder.pk,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_text')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)

    def test_user_can_copy_plugins_to_language(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'copy_language', page.pk)
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'TextPlugin'),
        ]
        placeholder = plugins[0].placeholder

        data = {
            'source_language': 'en',
            'target_language': translation.language,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_text')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            new_plugins = placeholder.get_plugins(translation.language)
            self.assertEqual(new_plugins.count(), len(plugins))

    def test_user_cant_copy_plugins_to_language(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'copy_language', page.pk)
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'TextPlugin'),
        ]
        placeholder = plugins[0].placeholder

        data = {
            'source_language': 'en',
            'target_language': translation.language,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_text')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            new_plugins = placeholder.get_plugins(translation.language)
            self.assertEqual(new_plugins.count(), 0)

    # Placeholder related tests

    def test_can_clear_placeholder(self):
        """
        Ensures a user without delete plugin permissions
        cannot clear a page placeholder that contains said plugin.
        """
        page_en = create_page("EmptyPlaceholderTestPage (EN)", "nav_playground.html", "en")
        ph = page_en.placeholders.get(slot="body")

        # add text plugin
        add_plugin(ph, "TextPlugin", "en", body="Hello World EN 1")
        add_plugin(ph, "TextPlugin", "en", body="Hello World EN 2")

        # add a link plugin to make sure we test diversity
        add_plugin(ph, "LinkPlugin", "en", name='link-1')
        add_plugin(ph, "LinkPlugin", "en", name='link-2')

        # Staff user has basic page permissions but no
        # plugin permissions.
        staff = self._get_staff_user()
        endpoint = '%s?language=en' % admin_reverse('cms_page_clear_placeholder', args=[ph.pk])

        # Give the staff user permission to delete text plugins
        staff.user_permissions.add(Permission.objects.get(codename='delete_text'))
        # Give the staff user permission to delete link plugins
        staff.user_permissions.add(Permission.objects.get(codename='delete_link'))

        with self.login_user_context(staff):
            response = self.client.post(endpoint, {'test': 0})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ph.get_plugins('en').count(), 0)

    def test_cant_clear_placeholder(self):
        page_en = create_page("EmptyPlaceholderTestPage (EN)", "nav_playground.html", "en")
        ph = page_en.placeholders.get(slot="body")

        # add text plugin
        add_plugin(ph, "TextPlugin", "en", body="Hello World EN 1")
        add_plugin(ph, "TextPlugin", "en", body="Hello World EN 2")

        # add a link plugin to make sure we test diversity
        add_plugin(ph, "LinkPlugin", "en", name='link-1')
        add_plugin(ph, "LinkPlugin", "en", name='link-2')

        # Staff user has basic page permissions but no
        # plugin permissions.
        staff = self._get_staff_user()
        endpoint = '%s?language=en' % admin_reverse('cms_page_clear_placeholder', args=[ph.pk])

        with self.login_user_context(staff):
            response = self.client.post(endpoint, {'test': 0})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ph.get_plugins('en').count(), 4)

        # Give the staff user permission to delete text plugins
        staff.user_permissions.add(Permission.objects.get(codename='delete_text'))

        with self.login_user_context(staff):
            response = self.client.post(endpoint, {'test': 0})

        # Operation results in 403 because staff user does not have
        # permission to delete links
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ph.get_plugins('en').count(), 4)


@override_settings(CMS_PERMISSION=True)
class PermissionsOnPageTest(PermissionsTestCase):
    pass


class PermissionsOffTest(PermissionsTestCase):

    def test_can_delete(self):
        admin_user, staff_user = self._get_guys()
        create_page("home", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        body = page.placeholders.get(slot='body')
        add_plugin(body, 'TextPlugin', 'en', body='text')
        page.publish('en')

        # CMS_PERMISSION is set to False and user does not
        # have permission to delete any plugins but the page
        # has no plugins.
        with self.settings(CMS_PERMISSION=False):
            with self.login_user_context(staff_user):
                data = {'post': 'yes'}
                response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)

                # assert deleting page was successful
                self.assertRedirects(response, URL_CMS_PAGE)
                self.assertFalse(Page.objects.filter(pk=page.pk).exists())

        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        body = page.placeholders.get(slot='body')
        add_plugin(body, 'TextPlugin', 'en', body='text')
        page.publish('en')

        # CMS_PERMISSION is set to False and user does not
        # have permission to delete any plugin
        with self.settings(CMS_PERMISSION=False):
            with self.login_user_context(staff_user):
                data = {'post': 'yes'}
                response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)

                # assert deleting page was unsuccessful
                self.assertEqual(response.status_code, 403)
                self.assertTrue(Page.objects.filter(pk=page.pk).exists())

        # Give the staff user permission to delete text plugins
        staff_user.user_permissions.add(Permission.objects.get(codename='delete_text'))

        # CMS_PERMISSION is set to False and user has
        # permission to delete text plugins
        with self.settings(CMS_PERMISSION=False):
            with self.login_user_context(staff_user):
                data = {'post': 'yes'}
                response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)

                # assert deleting page was successful
                self.assertRedirects(response, URL_CMS_PAGE)
                self.assertFalse(Page.objects.filter(pk=page.pk).exists())

    def test_cant_delete(self):
        admin_user, staff_user = self._get_guys()
        create_page("home", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        body = page.placeholders.get(slot='body')
        add_plugin(body, 'TextPlugin', 'en', body='text')
        page.publish('en')

        # CMS_PERMISSION is set to False and user does not
        # have permission to delete any plugins but the page
        # has no plugins.
        with self.settings(CMS_PERMISSION=False):
            with self.login_user_context(staff_user):
                data = {'post': 'yes'}
                response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)

                # assert deleting page was successful
                self.assertRedirects(response, URL_CMS_PAGE)
                self.assertFalse(Page.objects.filter(pk=page.pk).exists())

        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        body = page.placeholders.get(slot='body')
        add_plugin(body, 'TextPlugin', 'en', body='text')
        page.publish('en')

        # CMS_PERMISSION is set to False and user does not
        # have permission to delete any plugin
        with self.settings(CMS_PERMISSION=False):
            with self.login_user_context(staff_user):
                data = {'post': 'yes'}
                response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)

                # assert deleting page was unsuccessful
                self.assertEqual(response.status_code, 403)
                self.assertTrue(Page.objects.filter(pk=page.pk).exists())

        # Give the staff user permission to delete text plugins
        staff_user.user_permissions.add(Permission.objects.get(codename='delete_text'))

        # CMS_PERMISSION is set to False and user has
        # permission to delete text plugins
        with self.settings(CMS_PERMISSION=False):
            with self.login_user_context(staff_user):
                data = {'post': 'yes'}
                response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)

                # assert deleting page was successful
                self.assertRedirects(response, URL_CMS_PAGE)
                self.assertFalse(Page.objects.filter(pk=page.pk).exists())


@override_settings(ROOT_URLCONF='cms.test_utils.project.noadmin_urls')
class NoAdminPageTests(CMSTestCase):

    def test_get_page_from_request_fakeadmin_nopage(self):
        noadmin_apps = [app for app in installed_apps() if app != 'django.contrib.admin']
        with self.settings(INSTALLED_APPS=noadmin_apps):
            request = self.get_request('/en/admin/')
            page = get_page_from_request(request)
            self.assertEqual(page, None)
