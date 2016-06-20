# -*- coding: utf-8 -*-
import datetime

from django.core.cache import cache
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, AnonymousUser
from django.contrib.admin.sites import site, AdminSite
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
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


@override_settings(CMS_PERMISSION=True)
class PageAdminPermissionsOnTest(PageAdminTestBase):

    def test_pages_in_admin_index(self):
        pass

    def test_pages_not_in_admin_index(self):
        pass

    def test_page_can_edit(self):
        pass

    def test_page_cant_edit(self):
        pass

    def test_get_permissions(self):
        page = create_page('test-page', 'nav_playground.html', 'en')
        url = admin_reverse('cms_page_get_permissions', args=(page.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/en/admin/login/?next=%s' % (URL_CMS_PAGE_PERMISSIONS % page.pk))
        admin_user = self.get_superuser()
        with self.login_user_context(admin_user):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateNotUsed(response, 'admin/login.html')

    def test_delete_permissions(self):
        admin_user, staff_user = self._get_guys()
        create_page("home", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        body = page.placeholders.get(slot='body')
        add_plugin(body, 'TextPlugin', 'en', body='text')
        page.publish('en')

        # CMS_PERMISSION is set to True and staff user
        # has global permissions set.
        with self.settings(CMS_PERMISSION=True):
            with self.login_user_context(staff_user):
                data = {'post': 'yes'}
                response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)

                # assert deleting page was successful
                self.assertRedirects(response, URL_CMS_PAGE)
                self.assertFalse(Page.objects.filter(pk=page.pk).exists())

        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user, published=True)

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

    def test_delete_translation_permissions(self):
        admin_user, staff_user = self._get_guys()
        page = create_page("delete-page-translation", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        body = page.placeholders.get(slot='body')
        create_title("de", "delete-page-translation-2", page, slug="delete-page-translation-2")
        create_title("fr", "delete-page-translation-fr", page.reload(), slug="delete-page-translation-fr")
        add_plugin(body, 'TextPlugin', 'de', body='text')

        # add a link plugin but never give the user permission to delete it
        # all our tests target the german translation.
        # this asserts that a plugin in another language does not interfere
        # with deleting.
        link = add_plugin(body, 'LinkPlugin', 'en', name='link-1')

        # CMS_PERMISSION is set to True and staff user
        # has global permissions set.
        with self.settings(CMS_PERMISSION=True):
            with self.login_user_context(staff_user):
                response = self.client.post(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'de'})

                # assert deleting page was successful
                self.assertRedirects(response, URL_CMS_PAGE)
                self.assertFalse(page.title_set.filter(language='de').exists())
                # LinkPlugin should continue to be
                self.assertTrue(body.cmsplugin_set.filter(pk=link.pk).exists())

        # the API needs a fresh page object
        page = page.reload()
        create_title("de", "delete-page-translation-2", page.reload(), slug="delete-page-translation-2")
        add_plugin(body, 'TextPlugin', 'de', body='text')

        # CMS_PERMISSION is set to False and user does not
        # have permission to delete text plugins
        with self.settings(CMS_PERMISSION=False):
            with self.login_user_context(staff_user):
                response = self.client.post(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'de'})

                # assert deleting page was successful
                self.assertEqual(response.status_code, 403)
                self.assertTrue(page.title_set.filter(language='de').exists())
                # LinkPlugin should continue to be
                self.assertTrue(body.cmsplugin_set.filter(pk=link.pk).exists())

        # CMS_PERMISSION is set to False and user does not
        # have permission to delete any plugins but the translation
        # does not contain plugins
        with self.settings(CMS_PERMISSION=False):
            with self.login_user_context(staff_user):
                response = self.client.post(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'fr'})

                # assert deleting page was successful
                self.assertRedirects(response, URL_CMS_PAGE)
                self.assertFalse(page.title_set.filter(language='fr').exists())
                # LinkPlugin should continue to be
                self.assertTrue(body.cmsplugin_set.filter(pk=link.pk).exists())

        # Give the staff user permission to delete text plugins
        staff_user.user_permissions.add(Permission.objects.get(codename='delete_text'))

        # CMS_PERMISSION is set to False and user has
        # permission to delete text plugins
        with self.settings(CMS_PERMISSION=False):
            with self.login_user_context(staff_user):
                response = self.client.post(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'de'})

                # assert deleting page was successful
                self.assertRedirects(response, URL_CMS_PAGE)
                self.assertFalse(page.title_set.filter(language='de').exists())
                # LinkPlugin should continue to be
                self.assertTrue(body.cmsplugin_set.filter(pk=link.pk).exists())

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

    def test_permissioned_page_list(self):
        """
        Makes sure that a user with restricted page permissions can view
        the page list.
        """
        admin_user, normal_guy = self._get_guys(use_global_permissions=False)

        current_site = Site.objects.get(pk=1)
        page = create_page("Test page", "nav_playground.html", "en",
                           site=current_site, created_by=admin_user)

        PagePermission.objects.create(page=page, user=normal_guy)

        with self.login_user_context(normal_guy):
            resp = self.client.get(URL_CMS_PAGE)
            self.assertEqual(resp.status_code, 200)

    def test_edit_title_is_allowed_for_staff_user(self):
        """
        We check here both the permission on a single page, and the global permissions
        """
        user = self._create_user('user', is_staff=True)
        another_user = self._create_user('another_user', is_staff=True)

        page = create_page('A', 'nav_playground.html', 'en')
        admin_url = reverse("admin:cms_page_edit_title_fields", args=(
            page.pk, 'en'
        ))
        page_admin = PageAdmin(Page, None)
        page_admin._current_page = page

        username = getattr(user, get_user_model().USERNAME_FIELD)
        self.client.login(username=username, password=username)
        response = self.client.get(admin_url)
        self.assertEqual(response.status_code, 403)

        assign_user_to_page(page, user, grant_all=True)
        username = getattr(user, get_user_model().USERNAME_FIELD)
        self.client.login(username=username, password=username)
        response = self.client.get(admin_url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        self._give_cms_permissions(another_user)
        username = getattr(another_user, get_user_model().USERNAME_FIELD)
        self.client.login(username=username, password=username)
        response = self.client.get(admin_url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_edit_does_not_reset_apphook(self):
        """
        Makes sure that if a non-superuser with no rights to edit advanced page
        fields edits a page, those advanced fields are not touched.
        """
        OLD_PAGE_NAME = 'Test Page'
        NEW_PAGE_NAME = 'Test page 2'
        REVERSE_ID = 'Test'
        APPLICATION_URLS = 'project.sampleapp.urls'

        admin_user, normal_guy = self._get_guys()

        current_site = Site.objects.get(pk=1)

        # The admin creates the page
        page = create_page(OLD_PAGE_NAME, "nav_playground.html", "en",
                           site=current_site, created_by=admin_user)
        page.reverse_id = REVERSE_ID
        page.save()
        title = page.get_title_obj()
        title.has_url_overwrite = True

        title.save()
        page.application_urls = APPLICATION_URLS
        page.save()
        self.assertEqual(page.get_title(), OLD_PAGE_NAME)
        self.assertEqual(page.reverse_id, REVERSE_ID)
        self.assertEqual(page.application_urls, APPLICATION_URLS)

        # The user edits the page (change the page name for ex.)
        page_data = {
            'title': NEW_PAGE_NAME,
            'slug': page.get_slug(),
            'language': title.language,
            'site': page.site.pk,
            'template': page.template,
            'pagepermission_set-TOTAL_FORMS': 0,
            'pagepermission_set-INITIAL_FORMS': 0,
            'pagepermission_set-MAX_NUM_FORMS': 0,
            'pagepermission_set-2-TOTAL_FORMS': 0,
            'pagepermission_set-2-INITIAL_FORMS': 0,
            'pagepermission_set-2-MAX_NUM_FORMS': 0,
        }

        with self.login_user_context(normal_guy):
            resp = self.client.post(URL_CMS_PAGE_CHANGE % page.pk, page_data,
                                    follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateNotUsed(resp, 'admin/login.html')
            page = Page.objects.get(pk=page.pk)
            self.assertEqual(page.get_title(), NEW_PAGE_NAME)
            self.assertEqual(page.reverse_id, REVERSE_ID)
            self.assertEqual(page.application_urls, APPLICATION_URLS)
            title = page.get_title_obj()
            # The admin edits the page (change the page name for ex.)
            page_data = {
                'title': OLD_PAGE_NAME,
                'slug': page.get_slug(),
                'language': title.language,
                'site': page.site.pk,
                'template': page.template,
                'reverse_id': page.reverse_id,
            }

        with self.login_user_context(admin_user):
            resp = self.client.post(URL_CMS_PAGE_ADVANCED_CHANGE % page.pk, page_data,
                                    follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateNotUsed(resp, 'admin/login.html')
            resp = self.client.post(URL_CMS_PAGE_CHANGE % page.pk, page_data,
                                    follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateNotUsed(resp, 'admin/login.html')
            page = Page.objects.get(pk=page.pk)

            self.assertEqual(page.get_title(), OLD_PAGE_NAME)
            self.assertEqual(page.reverse_id, REVERSE_ID)
            self.assertEqual(page.application_urls, '')

    def test_edit_does_not_reset_page_adv_fields(self):
        """
        Makes sure that if a non-superuser with no rights to edit advanced page
        fields edits a page, those advanced fields are not touched.
        """
        OLD_PAGE_NAME = 'Test Page'
        NEW_PAGE_NAME = 'Test page 2'
        REVERSE_ID = 'Test'
        OVERRIDE_URL = 'my/override/url'

        admin_user, normal_guy = self._get_guys()

        current_site = Site.objects.get(pk=1)

        # The admin creates the page
        page = create_page(OLD_PAGE_NAME, "nav_playground.html", "en",
                           site=current_site, created_by=admin_user)
        page.reverse_id = REVERSE_ID
        page.save()
        title = page.get_title_obj()
        title.has_url_overwrite = True
        title.path = OVERRIDE_URL
        title.save()

        self.assertEqual(page.get_title(), OLD_PAGE_NAME)
        self.assertEqual(page.reverse_id, REVERSE_ID)
        self.assertEqual(title.overwrite_url, OVERRIDE_URL)

        # The user edits the page (change the page name for ex.)
        page_data = {
            'title': NEW_PAGE_NAME,
            'slug': page.get_slug(),
            'language': title.language,
            'site': page.site.pk,
            'template': page.template,
            'pagepermission_set-TOTAL_FORMS': 0,
            'pagepermission_set-INITIAL_FORMS': 0,
            'pagepermission_set-MAX_NUM_FORMS': 0,
            'pagepermission_set-2-TOTAL_FORMS': 0,
            'pagepermission_set-2-INITIAL_FORMS': 0,
            'pagepermission_set-2-MAX_NUM_FORMS': 0
        }
        # required only if user haves can_change_permission
        with self.login_user_context(normal_guy):
            resp = self.client.post(URL_CMS_PAGE_CHANGE % page.pk, page_data,
                                    follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateNotUsed(resp, 'admin/login.html')
            page = Page.objects.get(pk=page.pk)

            self.assertEqual(page.get_title(), NEW_PAGE_NAME)
            self.assertEqual(page.reverse_id, REVERSE_ID)
            title = page.get_title_obj()
            self.assertEqual(title.overwrite_url, OVERRIDE_URL)

        # The admin edits the page (change the page name for ex.)
        page_data = {
            'title': OLD_PAGE_NAME,
            'slug': page.get_slug(),
            'language': title.language,
            'site': page.site.pk,
            'template': page.template,
            'reverse_id': page.reverse_id,
            'pagepermission_set-TOTAL_FORMS': 0,  # required only if user haves can_change_permission
            'pagepermission_set-INITIAL_FORMS': 0,
            'pagepermission_set-MAX_NUM_FORMS': 0,
            'pagepermission_set-2-TOTAL_FORMS': 0,
            'pagepermission_set-2-INITIAL_FORMS': 0,
            'pagepermission_set-2-MAX_NUM_FORMS': 0
        }
        with self.login_user_context(admin_user):
            resp = self.client.post(URL_CMS_PAGE_CHANGE % page.pk, page_data,
                                    follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateNotUsed(resp, 'admin/login.html')
            page = Page.objects.get(pk=page.pk)

            self.assertEqual(page.get_title(), OLD_PAGE_NAME)
            self.assertEqual(page.reverse_id, REVERSE_ID)
            title = page.get_title_obj()
            self.assertEqual(title.overwrite_url, OVERRIDE_URL)


@override_settings(CMS_PERMISSION=True)
class PluginPermissionsOnTest(PageAdminTestBase):

    def test_plugin_add_requires_permissions(self):
        """User tries to add a plugin but has no permissions. He can add the plugin after he got the permissions"""
        admin = self._get_admin()
        self._give_cms_permissions(admin)

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='admin@django-cms.org', password='admin')
        else:
            self.client.login(username='admin', password='admin')

        url = admin_reverse('cms_page_add_plugin') + '?' + urlencode({
            'plugin_type': 'TextPlugin',
            'placeholder_id': self._placeholder.pk,
            'plugin_language': 'en',

        })
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 403)
        self._give_permission(admin, Text, 'add')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)

    def test_plugin_edit_requires_permissions(self):
        """User tries to edit a plugin but has no permissions. He can edit the plugin after he got the permissions"""
        plugin = self._create_plugin()
        _, normal_guy = self._get_guys()

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='test@test.com', password='test@test.com')
        else:
            self.client.login(username='test', password='test')

        url = admin_reverse('cms_page_edit_plugin', args=[plugin.id])
        response = self.client.post(url, dict())
        self.assertEqual(response.status_code, 403)
        # After he got the permissions, he can edit the plugin
        self._give_permission(normal_guy, Text, 'change')
        response = self.client.post(url, dict())
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_plugin_remove_requires_permissions(self):
        """User tries to remove a plugin but has no permissions. He can remove the plugin after he got the permissions"""
        plugin = self._create_plugin()
        _, normal_guy = self._get_guys()

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='test@test.com', password='test@test.com')
        else:
            self.client.login(username='test', password='test')

        url = admin_reverse('cms_page_delete_plugin', args=[plugin.pk])
        data = dict(plugin_id=plugin.id)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)
        # After he got the permissions, he can edit the plugin
        self._give_permission(normal_guy, Text, 'delete')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_plugin_move_requires_permissions(self):
        """User tries to move a plugin but has no permissions. He can move the plugin after he got the permissions"""
        plugin = self._create_plugin()
        _, normal_guy = self._get_guys()

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='test@test.com', password='test@test.com')
        else:
            self.client.login(username='test', password='test')

        url = admin_reverse('cms_page_move_plugin')
        data = dict(plugin_id=plugin.id,
                    placeholder_id=self._placeholder.pk,
                    plugin_parent='',
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)
        # After he got the permissions, he can edit the plugin
        self._give_permission(normal_guy, Text, 'change')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_plugins_copy_requires_permissions(self):
        """User tries to copy plugin but has no permissions. He can copy plugins after he got the permissions"""
        plugin = self._create_plugin()
        _, normal_guy = self._get_guys()

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='test@test.com', password='test@test.com')
        else:
            self.client.login(username='test', password='test')

        url = admin_reverse('cms_page_copy_plugins')
        data = dict(source_plugin_id=plugin.id,
                    source_placeholder_id=self._placeholder.pk,
                    source_language='en',
                    target_language='fr',
                    target_placeholder_id=self._placeholder.pk,
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)
        # After he got the permissions, he can edit the plugin
        self._give_permission(normal_guy, Text, 'add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_plugins_copy_language(self):
        """User tries to copy plugin but has no permissions. He can copy plugins after he got the permissions"""
        self._create_plugin()
        _, normal_guy = self._get_guys()

        if get_user_model().USERNAME_FIELD != 'email':
            self.client.login(username='test', password='test')
        else:
            self.client.login(username='test@test.com', password='test@test.com')

        self.assertEqual(1, CMSPlugin.objects.all().count())
        url = admin_reverse('cms_page_copy_language', args=[self._page.pk])
        data = dict(
            source_language='en',
            target_language='fr',
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)
        # After he got the permissions, he can edit the plugin
        self._give_permission(normal_guy, Text, 'add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertEqual(2, CMSPlugin.objects.all().count())

    def test_plugin_add_with_permissions_redirects(self):
        admin_user = self._get_admin()
        self._give_cms_permissions(admin_user)
        self._give_permission(admin_user, Text, 'add')

        username = getattr(admin_user, get_user_model().USERNAME_FIELD)
        self.client.login(username=username, password='admin')

        url = admin_reverse('cms_page_add_plugin') + '?' + urlencode({
            'plugin_type': 'TextPlugin',
            'placeholder_id': self._placeholder.pk,
            'plugin_language': 'en',
        })
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)


@override_settings(CMS_PERMISSION=True)
class PlaceholderPermissionOnTest(PageAdminTestBase):
    pass

    def test_clear_placeholder_permissions_page(self):
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

        # Give the staff user permission to delete link plugins
        staff.user_permissions.add(Permission.objects.get(codename='delete_link'))

        with self.login_user_context(staff):
            response = self.client.post(endpoint, {'test': 0})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ph.get_plugins('en').count(), 0)


@override_settings(ROOT_URLCONF='cms.test_utils.project.noadmin_urls')
class NoAdminPageTests(CMSTestCase):

    def test_get_page_from_request_fakeadmin_nopage(self):
        noadmin_apps = [app for app in installed_apps() if app != 'django.contrib.admin']
        with self.settings(INSTALLED_APPS=noadmin_apps):
            request = self.get_request('/en/admin/')
            page = get_page_from_request(request)
            self.assertEqual(page, None)
