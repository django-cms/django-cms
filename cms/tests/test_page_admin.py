# -*- coding: utf-8 -*-
import datetime

from django.core.cache import cache
from django.contrib import admin
from django.contrib.sites.models import Site
from django.forms.models import model_to_dict
from django.http import HttpRequest
from django.test.html import HTMLParseError, Parser
from django.test.utils import override_settings
from django.utils import six
from django.utils.encoding import force_text
from django.utils.timezone import now as tz_now

from cms import constants
from cms.admin.forms import AdvancedSettingsForm
from cms.admin.pageadmin import PageAdmin
from cms.api import create_page, add_plugin, create_title
from cms.constants import (
    PUBLISHER_STATE_DEFAULT,
    PUBLISHER_STATE_DIRTY,
    PUBLISHER_STATE_PENDING,
)
from cms.middleware.user import CurrentUserMiddleware
from cms.models.pagemodel import Page
from cms.models.permissionmodels import PagePermission
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import EmptyTitle, Title
from cms.test_utils.testcases import (
    CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_MOVE,
    URL_CMS_PAGE_ADVANCED_CHANGE, URL_CMS_PAGE_CHANGE, URL_CMS_PAGE_ADD
)
from cms.test_utils.util.context_managers import LanguageOverride, UserLoginContext
from cms.utils import get_cms_setting
from cms.utils.compat.dj import installed_apps
from cms.utils.i18n import force_language
from cms.utils.page_resolver import get_page_from_request
from cms.utils.urlutils import admin_reverse


class PageTreeLiParser(Parser):

    def handle_starttag(self, tag, attrs):
        # We have to strip out attributes from the <li>
        # tags in order to compare the values only
        # Otherwise we'd have to include all attributes
        # which in this case is not optimal because there's too many
        # and would require us to hardcode a bunch of stuff here
        if tag == 'li':
            attrs = []
        Parser.handle_starttag(self, tag, attrs)


class PageTreeOptionsParser(Parser):

    def handle_starttag(self, tag, attrs):
        # This parser only cares about the options on the right side
        # of the page tree for each page.
        if tag == 'li' and attrs and attrs[-1][0] == 'data-coloptions':
            attrs = [attrs[-1]]
        Parser.handle_starttag(self, tag, attrs)


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

    def _add_plugin_to_page(self, page, plugin_type='LinkPlugin', language='en', publish=True):
        plugin_data = {
            'TextPlugin': {'body': '<p>text</p>'},
            'LinkPlugin': {'name': 'A Link', 'url': 'https://www.django-cms.org'},
        }
        placeholder = page.placeholders.get(slot='body')
        plugin = add_plugin(placeholder, plugin_type, language, **plugin_data[plugin_type])

        if publish:
            page.reload().publish(language)
        return plugin

    def _translation_exists(self, slug=None, title=None):
        if not slug:
            slug = 'permissions-de'

        lookup = Title.objects.filter(slug=slug)

        if title:
            lookup = lookup.filter(title=title)
        return lookup.exists()

    def _get_add_plugin_uri(self, page, language='en'):
        placeholder = page.placeholders.get(slot='body')
        uri = self.get_add_plugin_uri(
            placeholder=placeholder,
            plugin_type='LinkPlugin',
            language=language,
        )
        return uri

    def _get_page_data(self, **kwargs):
        site = Site.objects.get_current()
        data = {
            'title': 'permissions',
            'slug': 'permissions',
            'language': 'en',
            'site': site.pk,
            'template': 'nav_playground.html',
        }
        data.update(**kwargs)
        return data

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

    def create_page(self, title=None, **kwargs):
        return create_page(title or self._testMethodName,
                           "nav_playground.html", "en", **kwargs)


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

    def test_edit_page_sets_publisher_dirty(self):
        """
        Test that setting and changing a value for a title/page field
        will cause the title to be marked as dirty (pending changes).
        """
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_data)

        page = Page.objects.get(title_set__slug=page_data['slug'], publisher_is_draft=True)

        basic_fields = {
            'title': ('new title', 'new title 2'),
            'slug': ('new-slug', 'new-slug-2'),
            'page_title': ('new page title', 'new page title 2'),
            'menu_title': ('new menu title', 'new menu title 2'),
            'meta_description': ('new menu description', 'new menu description 2'),
        }
        advanced_fields = {
            'overwrite_url': ('title-override', 'title-override-2'),
            'redirect': ('/title-redirect/', '/title-redirect-2/'),
        }

        set_message = 'setting field {} is not updating publisher status'
        change_message = 'changing field {} is not updating publisher status'

        with self.login_user_context(superuser):
            endpoint = self.get_admin_url(Page, 'change', page.pk)

            for field, values in basic_fields.items():
                # Set the initial value
                page_data[field] = values[0]
                self.client.post(endpoint, page_data)
                self.assertTrue(page.reload().is_dirty('en'), set_message.format(field))

                # Reset the publisher dirty status
                page.reload().publish('en')

                # Change the initial value=
                page_data[field] = values[1]
                self.client.post(endpoint, page_data)
                self.assertTrue(page.reload().is_dirty('en'), change_message.format(field))

            endpoint = self.get_admin_url(Page, 'advanced', page.pk)

            for field, values in advanced_fields.items():
                # Set the initial value
                page_data[field] = values[0]
                self.client.post(endpoint, page_data)
                self.assertTrue(page.reload().is_dirty('en'), set_message.format(field))

                # Reset the publisher dirty status
                page.reload().publish('en')

                # Change the initial value
                page_data[field] = values[1]
                self.client.post(endpoint, page_data)
                self.assertTrue(page.reload().is_dirty('en'), change_message.format(field))

    def test_page_redirect_field_validation(self):
        superuser = self.get_superuser()
        data = self.get_new_page_data()

        with self.login_user_context(superuser):
            self.client.post(URL_CMS_PAGE_ADD, data)

        page = Page.objects.get(title_set__slug=data['slug'], publisher_is_draft=True)

        endpoint = URL_CMS_PAGE_ADVANCED_CHANGE % page.pk
        redirect_to = URL_CMS_PAGE

        with self.login_user_context(superuser):
            data['redirect'] = '/'
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)

        with self.login_user_context(superuser):
            data['redirect'] = '/hello'
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)

        with self.login_user_context(superuser):
            data['redirect'] = '/hello/'
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)

        with self.login_user_context(superuser):
            data['redirect'] = '../hello'
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)

        with self.login_user_context(superuser):
            data['redirect'] = '../hello/'
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)

        with self.login_user_context(superuser):
            data['redirect'] = 'javascript:alert(1)'
            # Asserts users can't insert javascript call
            response = self.client.post(endpoint, data)
            validation_error = '<ul class="errorlist"><li>Enter a valid URL.</li></ul>'
            self.assertContains(response, validation_error, html=True)

        with self.login_user_context(superuser):
            data['redirect'] = '<script>alert("test")</script>'
            # Asserts users can't insert javascript call
            response = self.client.post(endpoint, data)
            validation_error = '<ul class="errorlist"><li>Enter a valid URL.</li></ul>'
            self.assertContains(response, validation_error, html=True)

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

    def test_publish_with_pending_unpublished_descendants(self):
        # ref: https://github.com/divio/django-cms/issues/5900
        superuser = self.get_superuser()

        # Needed because the first page created is published automatically
        self.create_page("Home", published=False)
        ancestor = self.create_page("Ancestor", published=False)
        parent = self.create_page("Child", published=False, parent=ancestor)
        child = self.create_page("Child", published=False, parent=parent)

        with self.login_user_context(superuser):
            response = self.client.post(self.get_admin_url(Page, 'publish_page', child.pk, 'en'))

            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                child.reload().get_publisher_state("en"),
                PUBLISHER_STATE_PENDING
            )

            response = self.client.post(self.get_admin_url(Page, 'publish_page', parent.pk, 'en'))

            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                parent.reload().get_publisher_state("en"),
                PUBLISHER_STATE_PENDING
            )

            response = self.client.post(self.get_admin_url(Page, 'publish_page', ancestor.pk, 'en'))

            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                ancestor.reload().get_publisher_state("en"),
                PUBLISHER_STATE_DEFAULT
            )
            self.assertEqual(
                parent.reload().get_publisher_state("en"),
                PUBLISHER_STATE_DEFAULT
            )
            self.assertEqual(
                child.reload().get_publisher_state("en"),
                PUBLISHER_STATE_DEFAULT
            )

    def test_move_page_regression_5900(self):
        # ref: https://github.com/divio/django-cms/issues/5900
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_home = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_home)

            # Create parent page
            page_root = create_page("Parent", 'col_three.html', "de", published=False)

            # Create english translation
            create_title(
                "en",
                "parent-en",
                page=page_root,
                slug="parent-en"
            )

            # Create child pages
            page_child_1 = create_page(
                "Child 1",
                template=constants.TEMPLATE_INHERITANCE_MAGIC,
                language="de",
                parent=page_root,
                published=False
            )

            # Create english translation
            create_title(
                "en",
                "child-1-en",
                page=page_child_1,
                slug="child-1-en"
            )

            # Try to publish child english translation
            publish_endpoint = self.get_admin_url(Page, 'publish_page', page_child_1.pk, 'en')

            self.client.post(publish_endpoint)

            self.assertEqual(
                page_child_1.get_publisher_state("en"),
                PUBLISHER_STATE_PENDING,
            )

            # Publish the german translations for both the parent and child pages.
            # This will create the public versions for both.
            page_root.publish('de')
            page_child_1.publish('de')

            # Move page_child_1 to the root
            data = {
                "id": page_child_1.pk,
                "position": "2",
            }

            response = self.client.post(
                URL_CMS_PAGE_MOVE % page_child_1.pk,
                data,
            )
            self.assertEqual(response.status_code, 200)

            # Ensure move worked
            self.assertEqual(page_root.reload().get_descendants().count(), 0)

            # Move page_child_1 under its old parent
            # page_child_1 does not have a public version of its english translation
            data = {
                "id": page_child_1.pk,
                "target": page_root.pk,
                "position": "0",
            }
            response = self.client.post(
                URL_CMS_PAGE_MOVE % page_child_1.pk,
                data,
            )
            self.assertEqual(response.status_code, 200)

            # Ensure move worked
            self.assertEqual(page_root.reload().get_descendants().count(), 1)

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

    def _parse_page_tree(self, response, parser_class):
        content = response.content
        content = content.decode(response.charset)

        def _parse_html(html):
            parser = parser_class()
            parser.feed(html)
            parser.close()
            document = parser.root
            document.finalize()
            # Removing ROOT element if it's not necessary
            if len(document.children) == 1:
                if not isinstance(document.children[0], six.string_types):
                    document = document.children[0]
            return document

        try:
            dom = _parse_html(content)
        except HTMLParseError as e:
            standardMsg = '%s\n%s' % ("Response's content is not valid HTML", e.msg)
            self.fail(self._formatMessage(None, standardMsg))
        return dom

    def test_page_tree_regression_5892(self):
        # ref: https://github.com/divio/django-cms/issues/5892
        # Tests the escaping of characters for a german translation
        # in the page tree.
        superuser = self.get_superuser()

        create_page('Home', 'nav_playground.html', 'en')
        alpha = create_page('Alpha', 'nav_playground.html', 'en')
        create_page('Beta', 'nav_playground.html', 'en', parent=alpha)
        create_page('Gamma', 'nav_playground.html', 'en')

        with self.login_user_context(superuser):
            with force_language('de'):
                endpoint = admin_reverse('get_tree')
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)
                parsed = self._parse_page_tree(response, parser_class=PageTreeOptionsParser)
                content = force_text(parsed)
                self.assertIn(u'(Shift-Klick für erweiterte Einstellungen)', content)

    def test_page_get_tree_endpoint_flat(self):
        superuser = self.get_superuser()
        endpoint = admin_reverse('get_tree')

        create_page('Home', 'nav_playground.html', 'en')
        alpha = create_page('Alpha', 'nav_playground.html', 'en')
        create_page('Beta', 'nav_playground.html', 'en', parent=alpha)
        create_page('Gamma', 'nav_playground.html', 'en')

        tree = (
            '<li>\nHome\n</li>'
            '<li>\nAlpha\n</li>'
            '<li>\nGamma\n</li>'
        )

        with self.login_user_context(superuser):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            parsed = self._parse_page_tree(response, parser_class=PageTreeLiParser)
            content = force_text(parsed)
            self.assertIn(tree, content)
            self.assertNotIn('<li>\nBeta\n</li>', content)

    def test_page_get_tree_endpoint_nested(self):
        superuser = self.get_superuser()
        endpoint = admin_reverse('get_tree')

        create_page('Home', 'nav_playground.html', 'en')
        alpha = create_page('Alpha', 'nav_playground.html', 'en')
        create_page('Beta', 'nav_playground.html', 'en', parent=alpha)
        gamma = create_page('Gamma', 'nav_playground.html', 'en')
        create_page('Delta', 'nav_playground.html', 'en', parent=gamma)
        create_page('Theta', 'nav_playground.html', 'en')

        tree = (
            '<li>\nHome\n</li>'
            '<li>\nAlpha'
            '<ul>\n<li>\nBeta\n</li>\n</ul>\n</li>'
            '<li>\nGamma'
            '<ul>\n<li>\nDelta\n</li>\n</ul>\n</li>'
            '<li>\nTheta\n</li>'
        )

        data = {
            'openNodes[]': [alpha.pk, gamma.pk]
        }

        with self.login_user_context(superuser):
            response = self.client.get(endpoint, data=data)
            self.assertEqual(response.status_code, 200)
            parsed = self._parse_page_tree(response, parser_class=PageTreeLiParser)
            content = force_text(parsed)
            self.assertIn(tree, content)

    def test_page_changelist_search(self):
        superuser = self.get_superuser()
        endpoint = self.get_admin_url(Page, 'changelist')

        create_page('Home', 'nav_playground.html', 'en')
        alpha = create_page('Alpha', 'nav_playground.html', 'en')
        create_page('Beta', 'nav_playground.html', 'en', parent=alpha)
        create_page('Gamma', 'nav_playground.html', 'en')

        with self.login_user_context(superuser):
            response = self.client.get(endpoint, data={'q': 'alpha'})
            self.assertEqual(response.status_code, 200)
            parsed = self._parse_page_tree(response, parser_class=PageTreeLiParser)
            content = force_text(parsed)
            self.assertIn('<li>\nAlpha\n</li>', content)
            self.assertNotIn('<li>\nHome\n</li>', content)
            self.assertNotIn('<li>\nBeta\n</li>', content)
            self.assertNotIn('<li>\nGamma\n</li>', content)

    def test_global_limit_on_plugin_move(self):
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
                data = {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_1.pk, 'plugin_parent': ''}
                endpoint = self.get_move_plugin_uri(plugin_1)
                response = self.client.post(endpoint, data) # first
                self.assertEqual(response.status_code, 200)
                data = {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_2.pk, 'plugin_parent': ''}
                endpoint = self.get_move_plugin_uri(plugin_2)
                response = self.client.post(endpoint, data) # second
                self.assertEqual(response.status_code, 200)
                data = {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_3.pk, 'plugin_parent': ''}
                endpoint = self.get_move_plugin_uri(plugin_3)
                response = self.client.post(endpoint, data) # third
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content, b"This placeholder already has the maximum number of plugins (2).")

    def test_type_limit_on_plugin_move(self):
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
                data = {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_1.pk, 'plugin_parent': ''}
                endpoint = self.get_move_plugin_uri(plugin_1)
                response = self.client.post(endpoint, data) # first
                self.assertEqual(response.status_code, 200)
                data = {'placeholder_id': target_placeholder.pk, 'plugin_id': plugin_2.pk, 'plugin_parent': ''}
                endpoint = self.get_move_plugin_uri(plugin_1)
                response = self.client.post(endpoint, data) # second
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content,
                                 b"This placeholder already has the maximum number (1) of allowed Text plugins.")

    @override_settings(CMS_PLACEHOLDER_CACHE=True)
    def test_placeholder_cache_cleared_on_publish(self):
        page = self.get_page()
        staff_user = self.get_superuser()
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin', publish=False),
            self._add_plugin_to_page(page, 'LinkPlugin', publish=False),
        ]

        with self.login_user_context(staff_user):
            # Publish the page
            publish_endpoint = self.get_admin_url(Page, 'publish_page', page.pk, 'en')
            self.client.post(publish_endpoint)

        response = self.client.get(page.get_absolute_url())
        self.assertContains(response, '<p>text</p>', html=True)
        self.assertContains(response, '<a href="https://www.django-cms.org" >A Link</a>', html=True)

        placeholder = plugins[0].placeholder

        with self.login_user_context(staff_user):
            # Delete the plugins
            data = {'post': True}

            for plugin in plugins:
                endpoint = self.get_delete_plugin_uri(plugin)
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 302)
            self.assertEqual(placeholder.get_plugins('en').count(), 0)

        with self.login_user_context(staff_user):
            # Publish the page
            publish_endpoint = self.get_admin_url(Page, 'publish_page', page.pk, 'en')
            self.client.post(publish_endpoint)

        response = self.client.get(page.get_absolute_url())
        self.assertNotContains(response, '<p>text</p>', html=True)
        self.assertNotContains(response, '<a href="https://www.django-cms.org" >A Link</a>', html=True)

    def test_clear_placeholder_marks_page_as_dirty(self):
        page = self.get_page()
        staff_user = self.get_superuser()
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'LinkPlugin'),
        ]
        placeholder = plugins[0].placeholder
        endpoint = self.get_clear_placeholder_url(placeholder)

        with self.login_user_context(staff_user):
            self.assertEqual(page.reload().get_publisher_state("en"), PUBLISHER_STATE_DEFAULT)
            response = self.client.post(endpoint, {'test': ''})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(placeholder.get_plugins('en').count(), 0)
            self.assertEqual(page.reload().get_publisher_state("en"), PUBLISHER_STATE_DIRTY)


class PermissionsTestCase(PageTestBase):

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

    def _page_permission_exists(self, **kwargs):
        return PagePermission.objects.filter(**kwargs).exists()

    def _get_page_permissions_data(self, **kwargs):
        if 'id' in kwargs:
            initial = 1
        else:
            initial = 0

        data = {
            'language': 'en',
            'limit_visibility_in_menu': '',
            'pagepermission_set-TOTAL_FORMS': 0,
            'pagepermission_set-INITIAL_FORMS': 0,
            'pagepermission_set-MAX_NUM_FORMS': 0,
            'pagepermission_set-2-TOTAL_FORMS': 1,
            'pagepermission_set-2-INITIAL_FORMS': initial,
            'pagepermission_set-2-MIN_NUM_FORMS': 0,
            'pagepermission_set-2-MAX_NUM_FORMS': 1000,
            'pagepermission_set-2-0-id': '',
            'pagepermission_set-2-0-page': '',
            'pagepermission_set-2-0-user': '',
            'pagepermission_set-2-0-group': '',
            'pagepermission_set-2-0-can_change': 'on',
            'pagepermission_set-2-0-can_change_permissions': 'on',
            'pagepermission_set-2-0-grant_on': 5,
        }

        non_inline = ('language', 'limit_visibility_in_menu')

        for attr, value in kwargs.items():
            if attr not in non_inline:
                attr = 'pagepermission_set-2-0-{}'.format(attr)
            data[attr] = value
        return data

    def _get_page_view_restrictions_data(self, **kwargs):
        if 'id' in kwargs:
            initial = 1
        else:
            initial = 0

        data = {
            'language': 'en',
            'limit_visibility_in_menu': '',
            'pagepermission_set-TOTAL_FORMS': 1,
            'pagepermission_set-INITIAL_FORMS': initial,
            'pagepermission_set-MIN_NUM_FORMS': 0,
            'pagepermission_set-MAX_NUM_FORMS': 1000,
            'pagepermission_set-0-id': '',
            'pagepermission_set-0-page': '',
            'pagepermission_set-0-user': '',
            'pagepermission_set-0-group': '',
            'pagepermission_set-0-can_view': 'on',
            'pagepermission_set-0-grant_on': 5,
            'pagepermission_set-2-TOTAL_FORMS': 0,
            'pagepermission_set-2-INITIAL_FORMS': 0,
            'pagepermission_set-2-MIN_NUM_FORMS': 0,
            'pagepermission_set-2-MAX_NUM_FORMS': 1000,
        }

        non_inline = ('language', 'limit_visibility_in_menu')

        for attr, value in kwargs.items():
            if attr not in non_inline:
                attr = 'pagepermission_set-0-{}'.format(attr)
            data[attr] = value
        return data


@override_settings(CMS_PERMISSION=True)
class PermissionsOnGlobalTest(PermissionsTestCase):
    """
    Tests all user interactions with the page admin
    while permissions are set to True and user has
    global permissions.
    """

    def test_pages_in_admin_index(self):
        """
        User can see the "Pages" section the admin
        if he has change permissions on the Page model
        and he has global change permissions.
        """
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
        """
        User can't see the "Pages" section the admin
        if he does not have change permissions on the Page model
        and/or does not have global change permissions.
        """
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
        """
        User can edit page settings if he has change permissions
        on the Page model and and he has global change permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'change', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()

        data = self._get_page_data(slug='permissions-2')

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertTrue(self._translation_exists(slug='permissions-2'))

    def test_user_cant_edit_page_settings(self):
        """
        User can't edit page settings if he does not
        have change permissions on the Page model and/or
        does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'change', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        data = self._get_page_data(slug='permissions-2')

        self.add_permission(staff_user, 'change_page')
        gp = self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._translation_exists(slug='permissions-2'))

        self.remove_permission(staff_user, 'change_page')
        gp.can_change = True
        gp.save(update_fields=['can_change'])

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._translation_exists(slug='permissions-2'))

    def test_user_can_edit_advanced_page_settings(self):
        """
        User can edit advanced page settings if he has change permissions
        on the Page model, global change permissions and
        global change advanced settings permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'advanced', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()

        data = self._get_page_data(reverse_id='permissions-2')

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertTrue(self._page_exists(reverse_id='permissions-2'))

    def test_user_cant_edit_advanced_page_settings(self):
        """
        User can't edit advanced page settings if he does not
        have change permissions on the Page model,
        does not have global change permissions and/or
        does not have global change advanced settings permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'advanced', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        data = self._get_page_data(reverse_id='permissions-2')

        self.add_permission(staff_user, 'change_page')
        gp = self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_advanced_settings=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._page_exists(reverse_id='permissions-2'))

        self.remove_permission(staff_user, 'change_page')
        gp.can_change = True
        gp.save(update_fields=['can_change'])

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._page_exists(reverse_id='permissions-2'))

    def test_user_can_delete_empty_page(self):
        """
        User can delete an empty page if he has delete & change permissions
        on the Page model and he has global delete & change permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_change=True, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._page_exists())

    def test_user_cant_delete_empty_page(self):
        """
        User can't delete an empty page if he does not
        have delete permissions on the Page model and/or
        does not have global delete permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'delete_page')
        gp = self.add_global_permission(staff_user, can_change=True, can_delete=False)

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

        self.remove_permission(staff_user, 'delete_page')
        gp.can_delete = True
        gp.save(update_fields=['can_delete'])

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

    def test_user_can_delete_non_empty_page(self):
        """
        User can delete a page with plugins if he has delete & change permissions
        on the Page model, delete permissions on the plugins in the page
        translations and global delete & change permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()

        self._add_plugin_to_page(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_global_permission(staff_user, can_change=True, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._page_exists())

    def test_user_cant_delete_non_empty_page(self):
        """
        User can't delete a page with plugins if he
        does not have delete permissions on the Page model,
        does not have delete permissions on the plugins
        in the page translations, and/or does not have
        global delete permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        self._add_plugin_to_page(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        gp = self.add_global_permission(staff_user, can_change=True, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

        self.remove_permission(staff_user, 'delete_page')
        gp.can_delete = True
        gp.save(update_fields=['can_delete'])

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

    def test_user_can_delete_empty_translation(self):
        """
        User can delete an empty translation if he has
        delete & change permissions on the Page model and he has
        global delete & change permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_change=True, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'language': translation.language}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._translation_exists())

    def test_user_cant_delete_empty_translation(self):
        """
        User can't delete an empty translation if he does not
        have delete permissions on the Page model and/or
        does not have global delete permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        gp = self.add_global_permission(staff_user, can_change=True, can_delete=False)

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

        self.remove_permission(staff_user, 'delete_page')
        gp.can_delete = True
        gp.save(update_fields=['can_delete'])

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

    def test_user_can_delete_non_empty_translation(self):
        """
        User can delete a translation with plugins if he has delete & change permissions
        on the Page model, delete permissions on the plugins in the translation
        and global delete & change permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self._add_plugin_to_page(page, language=translation.language)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_global_permission(staff_user, can_change=True, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'language': translation.language}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._translation_exists())

    def test_user_cant_delete_non_empty_translation(self):
        """
        User can't delete a translation with plugins if he
        does not have delete permissions on the Page model,
        does not have delete permissions on the plugins in the translation,
        and/or does not have global delete permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self._add_plugin_to_page(page, language=translation.language)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_change=True, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

    def test_user_can_revert_non_empty_page_to_live(self):
        """
        User can revert a page to live with plugins if he has change permissions
        on the Page model, delete permissions on the plugins in the translation
        being reverted and page change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(
            Page,
            'revert_to_live',
            page.pk,
            translation.language,
        )
        live_page = page.publisher_public
        draft_plugins = page.placeholders.get(slot='body').get_plugins(translation.language)
        live_plugins = live_page.placeholders.get(slot='body').get_plugins(translation.language)

        self._add_plugin_to_page(page, language=translation.language)

        page.publish(translation.language)

        self._add_plugin_to_page(page, language=translation.language, publish=False)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            self.assertEqual(draft_plugins.count(), 2)
            self.assertEqual(live_plugins.count(), 1)

            data = {'language': translation.language}

            self.client.post(endpoint, data)
            self.assertEqual(draft_plugins.count(), 1)
            self.assertEqual(live_plugins.count(), 1)

    def test_user_cant_revert_non_empty_page_to_live(self):
        """
        User can't revert a page with plugins to live if he
        does not have has change permissions on the Page model,
        delete permissions on the plugins in the translation
        being reverted and/or does not have page change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(
            Page,
            'revert_to_live',
            page.pk,
            translation.language,
        )
        live_page = page.publisher_public
        draft_plugins = page.placeholders.get(slot='body').get_plugins(translation.language)
        live_plugins = live_page.placeholders.get(slot='body').get_plugins(translation.language)

        self._add_plugin_to_page(page, language=translation.language)

        page.publish(translation.language)

        self._add_plugin_to_page(page, language=translation.language, publish=False)

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            self.assertEqual(draft_plugins.count(), 2)
            self.assertEqual(live_plugins.count(), 1)

            data = {'language': translation.language}
            response = self.client.post(endpoint, data)

            self.assertEqual(response.status_code, 403)
            self.assertEqual(draft_plugins.count(), 2)
            self.assertEqual(live_plugins.count(), 1)

    def test_user_can_view_page_permissions_summary(self):
        """
        All staff users can see the permissions summary for a page.
        """
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
        """
        Non staff users can't see the permissions summary for a page.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'get_permissions', page.pk)
        non_staff_user = self.get_standard_user()

        with self.login_user_context(non_staff_user):
            data = {'post': 'true'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, '/en/admin/login/?next=%s' % endpoint)

    def test_user_can_add_page_permissions(self):
        """
        User can add page permissions if he has
        change permissions on the Page model,
        add permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertTrue(self._page_permission_exists(user=staff_user_2))

    def test_user_cant_add_page_permissions(self):
        """
        User can't add page permissions if he
        does not have change permissions on the Page model,
        does not have add permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._page_permission_exists(user=staff_user_2))

    def test_user_can_edit_page_permissions(self):
        """
        User can edit page permissions if he has
        change permissions on the Page model,
        change permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)

        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_change_permissions=True
        )

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
            id=permission.pk,
            can_change_permissions=False,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertTrue(
                self._page_permission_exists(
                    user=staff_user_2,
                    can_change_permissions=False,
                )
            )

    def test_user_cant_edit_page_permissions(self):
        """
        User can't edit page permissions if he
        does not have change permissions on the Page model,
        does not have change permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)

        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_change_permissions=True
        )

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
            id=permission.pk,
            can_change_permissions=False,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(
                self._page_permission_exists(
                    user=staff_user_2,
                    can_change_permissions=False,
                )
            )

    def test_user_can_delete_page_permissions(self):
        """
        User can delete page permissions if he has
        change permissions on the Page model,
        delete permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)
        permission = self.add_page_permission(user=staff_user_2, page=page)

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
            id=permission.pk,
            DELETE='on',
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertFalse(self._page_permission_exists(user=staff_user_2))

    def test_user_cant_delete_page_permissions(self):
        """
        User can't delete page permissions if he
        does not have change permissions on the Page model,
        does not have delete permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)
        permission = self.add_page_permission(user=staff_user_2, page=page)

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
            id=permission.pk,
            DELETE='on',
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_permission_exists(user=staff_user_2))

    def test_user_can_add_page_view_restrictions(self):
        """
        User can add page view restrictions if he has
        change permissions on the Page model,
        add permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)

        data = self._get_page_view_restrictions_data(
            page=page.pk,
            user=staff_user_2.pk,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertTrue(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_user_cant_add_page_view_restrictions(self):
        """
        User can't add page view restrictions if he
        does not have change permissions on the Page model,
        does not have add permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)

        data = self._get_page_view_restrictions_data(
            page=page.pk,
            user=staff_user_2.pk,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_user_can_edit_page_view_restrictions(self):
        """
        User can edit page view restrictions if he has
        change permissions on the Page model,
        change permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)

        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_view=True,
            grant_on=1,
        )

        data = model_to_dict(permission, exclude=['group'])
        data['grant_on'] = 5

        data = self._get_page_view_restrictions_data(**data)
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertTrue(
                self._page_permission_exists(
                    user=staff_user_2,
                    grant_on=5,
                )
            )

    def test_user_cant_edit_page_view_restrictions(self):
        """
        User can't edit page view restrictions if he
        does not have change permissions on the Page model,
        does not have change permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)
        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_view=True,
            grant_on=1,
        )

        data = model_to_dict(permission, exclude=['group'])
        data['grant_on'] = 5

        data = self._get_page_view_restrictions_data(**data)
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(
                self._page_permission_exists(
                    user=staff_user_2,
                    grant_on=5,
                )
            )

    def test_user_can_delete_page_view_restrictions(self):
        """
        User can delete view restrictions if he has
        change permissions on the Page model,
        delete permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)
        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_view=True,
        )

        data = model_to_dict(permission, exclude=['group'])
        data['DELETE'] = True

        data = self._get_page_view_restrictions_data(**data)
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertFalse(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_user_cant_delete_page_view_restrictions(self):
        """
        User can't delete view restrictions if he
        does not have change permissions on the Page model,
        does not have delete permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        admin = self.get_superuser()
        page = self.get_permissions_test_page()
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)
        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_view=True,
        )

        data = model_to_dict(permission, exclude=['group'])
        data['DELETE'] = True

        data = self._get_page_view_restrictions_data(**data)
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_pagepermission')
        self.add_global_permission(
            staff_user,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_user_can_edit_title_fields(self):
        """
        User can edit title (translation) fields if he has
        global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        title = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'edit_title_fields', page.pk, title.language)

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = model_to_dict(title, fields=['title'])
            data['title'] = 'permissions-de-2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(self._translation_exists(title='permissions-de-2'))

    def test_user_cant_edit_title_fields(self):
        """
        User can't edit title (translation) fields if he does not have
        global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        title = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'edit_title_fields', page.pk, title.language)

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = model_to_dict(title, fields=['title'])
            data['title'] = 'permissions-de-2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._translation_exists(title='permissions-de-2'))

    # Plugin related tests

    def test_user_can_add_plugin(self):
        """
        User can add a plugin if he has change permissions
        on the Page model, add permissions on the plugin model
        and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.placeholders.get(slot='body')
        plugins = placeholder.get_plugins('en').filter(plugin_type='LinkPlugin')
        endpoint = self._get_add_plugin_uri(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = {'name': 'A Link', 'url': 'https://www.django-cms.org'}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(plugins.count(), 1)

    def test_user_cant_add_plugin(self):
        """
        User can't add a plugin if he
        does not have change permissions on the Page model,
        does not have add permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.placeholders.get(slot='body')
        plugins = placeholder.get_plugins('en').filter(plugin_type='LinkPlugin')
        endpoint = self._get_add_plugin_uri(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = {'name': 'A Link', 'url': 'https://www.django-cms.org'}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(plugins.count(), 0)

    def test_user_can_edit_plugin(self):
        """
        User can edit a plugin if he has change permissions
        on the Page model, change permissions on the plugin model
        and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_change_plugin_uri(plugin)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['name', 'url'])
            data['name'] = 'A link 2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            plugin.refresh_from_db()
            self.assertEqual(plugin.name, data['name'])

    def test_user_cant_edit_plugin(self):
        """
        User can't edit a plugin if he
        does not have change permissions on the Page model,
        does not have change permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_change_plugin_uri(plugin)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['name', 'url'])
            data['name'] = 'A link 2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            plugin.refresh_from_db()
            self.assertNotEqual(plugin.name, data['name'])

    def test_user_can_delete_plugin(self):
        """
        User can delete a plugin if he has change permissions
        on the Page model, delete permissions on the plugin model
        and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_delete_plugin_uri(plugin)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = {'post': True}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertFalse(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_user_cant_delete_plugin(self):
        """
        User can't delete a plugin if he
        does not have change permissions on the Page model,
        does not have delete permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_delete_plugin_uri(plugin)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = {'post': True}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_user_can_move_plugin(self):
        """
        User can move a plugin if he has change permissions
        on the Page model, change permissions on the plugin model
        and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_move_plugin_uri(plugin)
        source_placeholder = plugin.placeholder
        target_placeholder = page.placeholders.get(slot='right-column')

        data = {
            'plugin_id': plugin.pk,
            'placeholder_id': target_placeholder.pk,
            'plugin_parent': '',
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
            self.assertFalse(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

    def test_user_cant_move_plugin(self):
        """
        User can't move a plugin if he
        does not have change permissions on the Page model,
        does not have change permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_move_plugin_uri(plugin)
        source_placeholder = plugin.placeholder
        target_placeholder = page.placeholders.get(slot='right-column')

        data = {
            'plugin_id': plugin.pk,
            'placeholder_id': target_placeholder.pk,
            'plugin_parent': '',
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

    def test_user_can_copy_plugin(self):
        """
        User can copy a plugin if he has change permissions
        on the Page model, add permissions on the plugin model
        and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        translation = self._add_translation_to_page(page)
        endpoint = self.get_copy_plugin_uri(plugin)
        source_placeholder = plugin.placeholder
        target_placeholder = page.placeholders.get(slot='right-column')

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': source_placeholder.pk,
            'source_language': plugin.language,
            'target_language': translation.language,
            'target_placeholder_id': target_placeholder.pk,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk).exists())
            self.assertTrue(
                target_placeholder
                .get_plugins(translation.language)
                .filter(plugin_type=plugin.plugin_type)
                .exists()
            )

    def test_user_cant_copy_plugin(self):
        """
        User can't copy a plugin if he
        does not have change permissions on the Page model,
        does not have add permissions on the plugin model,
        and/or does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        translation = self._add_translation_to_page(page)
        endpoint = self.get_copy_plugin_uri(plugin)
        source_placeholder = plugin.placeholder
        target_placeholder = page.placeholders.get(slot='right-column')

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': source_placeholder.pk,
            'source_language': plugin.language,
            'target_language': translation.language,
            'target_placeholder_id': target_placeholder.pk,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk).exists())
            self.assertFalse(
                target_placeholder
                .get_plugins(translation.language)
                .filter(plugin_type=plugin.plugin_type)
                .exists()
            )

    def test_user_can_copy_plugins_to_language(self):
        """
        User can copy all plugins to another language if he has
        change permissions on the Page model, add permissions on the
        plugins being copied and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'copy_language', page.pk)
        plugins = [
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
        ]
        placeholder = plugins[0].placeholder

        data = {
            'source_language': 'en',
            'target_language': translation.language,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            new_plugins = placeholder.get_plugins(translation.language)
            self.assertEqual(new_plugins.count(), len(plugins))

    def test_user_cant_copy_plugins_to_language(self):
        """
        User can't copy all plugins to another language if he does have
        change permissions on the Page model, does not have add permissions
        on the plugins being copied and/or does not have global
        change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'copy_language', page.pk)
        plugins = [
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
        ]
        placeholder = plugins[0].placeholder

        data = {
            'source_language': 'en',
            'target_language': translation.language,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            new_plugins = placeholder.get_plugins(translation.language)
            self.assertEqual(new_plugins.count(), 0)

    # Placeholder related tests

    def test_user_can_clear_empty_placeholder(self):
        """
        User can clear an empty placeholder if he has change permissions
        on the Page model and global change permissions.
        """
        page = self.get_permissions_test_page()

        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.placeholders.get(slot='body')
        endpoint = self.get_clear_placeholder_url(placeholder)

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 302)

    def test_user_cant_clear_empty_placeholder(self):
        """
        User can't clear an empty placeholder if he does not have
        change permissions on the Page model and/or does not have
        global change permissions.
        """
        page = self.get_permissions_test_page()

        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.placeholders.get(slot='body')
        endpoint = self.get_clear_placeholder_url(placeholder)

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 403)

    def test_user_can_clear_non_empty_placeholder(self):
        """
        User can clear a placeholder with plugins if he has
        change permissions on the Page model, delete permissions
        on the plugin models in the placeholder and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'LinkPlugin'),
        ]
        placeholder = plugins[0].placeholder
        endpoint = self.get_clear_placeholder_url(placeholder)

        self.add_permission(staff_user, 'delete_text')
        self.add_permission(staff_user, 'delete_link')
        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(placeholder.get_plugins('en').count(), 0)

    def test_user_cant_clear_non_empty_placeholder(self):
        """
        User can't clear a placeholder with plugins if he does not have
        change permissions on the Page model, does not have delete
        permissions on the plugin models in the placeholder and/or
        does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'LinkPlugin'),
        ]
        placeholder = plugins[0].placeholder
        endpoint = self.get_clear_placeholder_url(placeholder)

        self.add_permission(staff_user, 'delete_text')
        self.add_permission(staff_user, 'delete_link')
        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 403)
            self.assertEqual(placeholder.get_plugins('en').count(), 2)

@override_settings(CMS_PERMISSION=True)
class PermissionsOnPageTest(PermissionsTestCase):
    """
    Tests all user interactions with the page admin
    while permissions are set to True and user has
    page permissions.
    """

    def setUp(self):
        self._permissions_page = self.get_permissions_test_page()

    def test_pages_in_admin_index(self):
        """
        User can see the "Pages" section the admin
        if he has change permissions on the Page model
        and he has global change permissions.
        """
        page = self._permissions_page
        endpoint = admin_reverse('app_list', args=['cms'])
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_page')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

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
        """
        User can't see the "Pages" section the admin
        if he does not have change permissions on the Page model
        and/or does not have global change permissions.
        """
        page = self._permissions_page
        endpoint = admin_reverse('app_list', args=['cms'])
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_page')
        self.add_page_permission(
            staff_user,
            page,
            can_change=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 404)

        endpoint = self.get_admin_url(Page, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)

    def test_user_can_edit_page_settings(self):
        """
        User can edit page settings if he has change permissions
        on the Page model and and he has global change permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'change', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()

        data = self._get_page_data(slug='permissions-2')

        self.add_permission(staff_user, 'change_page')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertTrue(self._translation_exists(slug='permissions-2'))

    def test_user_cant_edit_page_settings(self):
        """
        User can't edit page settings if he does not
        have change permissions on the Page model and/or
        does not have global change permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'change', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        data = self._get_page_data(slug='permissions-2')

        self.add_permission(staff_user, 'change_page')
        page_perm = self.add_page_permission(
            staff_user,
            page,
            can_change=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._translation_exists(slug='permissions-2'))

        self.remove_permission(staff_user, 'change_page')
        page_perm.can_change = True
        page_perm.save(update_fields=['can_change'])

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._translation_exists(slug='permissions-2'))

    def test_user_can_edit_advanced_page_settings(self):
        """
        User can edit advanced page settings if he has change permissions
        on the Page model, global change permissions and
        global change advanced settings permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'advanced', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()

        data = self._get_page_data(reverse_id='permissions-2')

        self.add_permission(staff_user, 'change_page')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertTrue(self._page_exists(reverse_id='permissions-2'))

    def test_user_cant_edit_advanced_page_settings(self):
        """
        User can't edit advanced page settings if he does not
        have change permissions on the Page model,
        does not have global change permissions and/or
        does not have global change advanced settings permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'advanced', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        data = self._get_page_data(reverse_id='permissions-2')

        self.add_permission(staff_user, 'change_page')
        page_perm = self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_advanced_settings=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._page_exists(reverse_id='permissions-2'))

        self.remove_permission(staff_user, 'change_page')
        page_perm.can_change = True
        page_perm.save(update_fields=['can_change'])

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._page_exists(reverse_id='permissions-2'))

    def test_user_can_delete_empty_page(self):
        """
        User can delete an empty page if he has delete & change permissions
        on the Page model and he has page delete & change permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_delete=True,
        )

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._page_exists())

    def test_user_cant_delete_empty_page(self):
        """
        User can't delete an empty page if he does not
        have delete permissions on the Page model and/or
        does not have global delete permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        page_perm = self.add_page_permission(
            staff_user,
            page,
            can_change=False,
            can_delete=False,
        )

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

        self.remove_permission(staff_user, 'delete_page')
        page_perm.can_delete = True
        page_perm.save(update_fields=['can_delete'])

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

    def test_user_can_delete_non_empty_page(self):
        """
        User can delete a page with plugins if he has delete permissions
        on the Page model, delete permissions on the plugins in the page
        translations and page delete & change permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()

        self._add_plugin_to_page(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_delete=True,
        )

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._page_exists())

    def test_user_cant_delete_non_empty_page(self):
        """
        User can't delete a page with plugins if he
        does not have delete permissions on the Page model,
        does not have delete permissions on the plugins
        in the page translations, and/or does not have
        global delete permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'delete', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        self._add_plugin_to_page(page)
        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')

        page_perm = self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_delete=True,
        )

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

        self.remove_permission(staff_user, 'delete_page')
        page_perm.can_delete = True
        page_perm.save(update_fields=['can_delete'])

        with self.login_user_context(staff_user):
            data = {'post': 'yes'}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_exists())

    def test_user_can_delete_empty_translation(self):
        """
        User can delete an empty translation if he has
        delete permissions on the Page model and he has
        page delete & change permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_delete=True,
        )

        with self.login_user_context(staff_user):
            data = {'language': translation.language}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._translation_exists())

    def test_user_cant_delete_empty_translation(self):
        """
        User can't delete an empty translation if he does not
        have delete permissions on the Page model and/or
        does not have global delete permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        page_perm = self.add_page_permission(
            staff_user,
            page,
            can_change=False,
            can_delete=False,
        )

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

        self.remove_permission(staff_user, 'delete_page')
        page_perm.can_delete = True
        page_perm.save(update_fields=['can_delete'])

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

    def test_user_can_delete_non_empty_translation(self):
        """
        User can delete a translation with plugins if he has delete permissions
        on the Page model, delete permissions on the plugins in the translation
        and page delete & change permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        redirect_to = self.get_admin_url(Page, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self._add_plugin_to_page(page, language=translation.language)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_delete=True,
        )

        with self.login_user_context(staff_user):
            data = {'language': translation.language}
            response = self.client.post(endpoint, data)

            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._translation_exists())

    def test_user_cant_delete_non_empty_translation(self):
        """
        User can't delete a translation with plugins if he
        does not have delete permissions on the Page model,
        does not have delete permissions on the plugins in the translation,
        and/or does not have global delete permissions.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'delete_translation', page.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)

        self._add_plugin_to_page(page, language=translation.language)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_delete=True,
        )

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

    def test_user_can_revert_non_empty_page_to_live(self):
        """
        User can revert a page to live with plugins if he has change permissions
        on the Page model, delete permissions on the plugins in the translation
        being reverted and page change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(
            Page,
            'revert_to_live',
            page.pk,
            translation.language,
        )
        live_page = page.publisher_public
        draft_plugins = page.placeholders.get(slot='body').get_plugins(translation.language)
        live_plugins = live_page.placeholders.get(slot='body').get_plugins(translation.language)

        self._add_plugin_to_page(page, language=translation.language)

        page.publish(translation.language)

        self._add_plugin_to_page(page, language=translation.language, publish=False)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

        with self.login_user_context(staff_user):
            self.assertEqual(draft_plugins.count(), 2)
            self.assertEqual(live_plugins.count(), 1)

            data = {'language': translation.language}

            self.client.post(endpoint, data)
            self.assertEqual(draft_plugins.count(), 1)
            self.assertEqual(live_plugins.count(), 1)

    def test_user_cant_revert_non_empty_page_to_live(self):
        """
        User can't revert a page with plugins to live if he
        does not have has change permissions on the Page model,
        delete permissions on the plugins in the translation
        being reverted and/or does not have page change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(
            Page,
            'revert_to_live',
            page.pk,
            translation.language,
        )
        live_page = page.publisher_public
        draft_plugins = page.placeholders.get(slot='body').get_plugins(translation.language)
        live_plugins = live_page.placeholders.get(slot='body').get_plugins(translation.language)

        self._add_plugin_to_page(page, language=translation.language)

        page.publish(translation.language)

        self._add_plugin_to_page(page, language=translation.language, publish=False)

        self.add_permission(staff_user, 'change_page')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

        with self.login_user_context(staff_user):
            self.assertEqual(draft_plugins.count(), 2)
            self.assertEqual(live_plugins.count(), 1)

            data = {'language': translation.language}
            response = self.client.post(endpoint, data)

            self.assertEqual(response.status_code, 403)
            self.assertEqual(draft_plugins.count(), 2)
            self.assertEqual(live_plugins.count(), 1)

    def test_user_can_add_page_permissions(self):
        """
        User can add page permissions if he has
        change permissions on the Page model,
        add permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertTrue(self._page_permission_exists(user=staff_user_2))

    def test_user_cant_add_page_permissions(self):
        """
        User can't add page permissions if he
        does not have change permissions on the Page model,
        does not have add permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._page_permission_exists(user=staff_user_2))

    def test_user_can_edit_page_permissions(self):
        """
        User can edit page permissions if he has
        change permissions on the Page model,
        change permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)

        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_change_permissions=True
        )

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
            id=permission.pk,
            can_change_permissions=False,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertTrue(
                self._page_permission_exists(
                    user=staff_user_2,
                    can_change_permissions=False,
                )
            )

    def test_user_cant_edit_page_permissions(self):
        """
        User can't edit page permissions if he
        does not have change permissions on the Page model,
        does not have change permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)

        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_change_permissions=True
        )

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
            id=permission.pk,
            can_change_permissions=False,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(
                self._page_permission_exists(
                    user=staff_user_2,
                    can_change_permissions=False,
                )
            )

    def test_user_can_delete_page_permissions(self):
        """
        User can delete page permissions if he has
        change permissions on the Page model,
        delete permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)
        permission = self.add_page_permission(user=staff_user_2, page=page)

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
            id=permission.pk,
            DELETE='on',
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertFalse(self._page_permission_exists(user=staff_user_2))

    def test_user_cant_delete_page_permissions(self):
        """
        User can't delete page permissions if he
        does not have change permissions on the Page model,
        does not have delete permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)
        permission = self.add_page_permission(user=staff_user_2, page=page)

        data = self._get_page_permissions_data(
            page=page.pk,
            user=staff_user_2.pk,
            id=permission.pk,
            DELETE='on',
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_permission_exists(user=staff_user_2))

    def test_user_can_add_page_view_restrictions(self):
        """
        User can add page view restrictions if he has
        change permissions on the Page model,
        add permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)

        data = self._get_page_view_restrictions_data(
            page=page.pk,
            user=staff_user_2.pk,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertTrue(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_user_cant_add_page_view_restrictions(self):
        """
        User can't add page view restrictions if he
        does not have change permissions on the Page model,
        does not have add permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)

        data = self._get_page_view_restrictions_data(
            page=page.pk,
            user=staff_user_2.pk,
        )
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_user_can_edit_page_view_restrictions(self):
        """
        User can edit page view restrictions if he has
        change permissions on the Page model,
        change permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)

        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_view=True,
            grant_on=1,
        )

        data = model_to_dict(permission, exclude=['group'])
        data['grant_on'] = 5

        data = self._get_page_view_restrictions_data(**data)
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertTrue(
                self._page_permission_exists(
                    user=staff_user_2,
                    grant_on=5,
                )
            )

    def test_user_cant_edit_page_view_restrictions(self):
        """
        User can't edit page view restrictions if he
        does not have change permissions on the Page model,
        does not have change permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)
        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_view=True,
            grant_on=1,
        )

        data = model_to_dict(permission, exclude=['group'])
        data['grant_on'] = 5

        data = self._get_page_view_restrictions_data(**data)
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(
                self._page_permission_exists(
                    user=staff_user_2,
                    grant_on=5,
                )
            )

    def test_user_can_delete_page_view_restrictions(self):
        """
        User can delete view restrictions if he has
        change permissions on the Page model,
        delete permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)
        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_view=True,
        )

        data = model_to_dict(permission, exclude=['group'])
        data['DELETE'] = True

        data = self._get_page_view_restrictions_data(**data)
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, endpoint)
            self.assertFalse(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_user_cant_delete_page_view_restrictions(self):
        """
        User can't delete view restrictions if he
        does not have change permissions on the Page model,
        does not have delete permissions on the PagePermission model,
        does not have global change permission,
        and/or does not have global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'permissions', page.pk) + '?language=en'
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=staff_user)
        permission = self.add_page_permission(
            user=staff_user_2,
            page=page,
            can_view=True,
        )

        data = model_to_dict(permission, exclude=['group'])
        data['DELETE'] = True

        data = self._get_page_view_restrictions_data(**data)
        data['_continue'] = '1'

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_pagepermission')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_user_can_edit_title_fields(self):
        """
        User can edit title (translation) fields if he has
        global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        title = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'edit_title_fields', page.pk, title.language)

        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )
        self.add_permission(staff_user, 'change_page')

        with self.login_user_context(staff_user):
            data = model_to_dict(title, fields=['title'])
            data['title'] = 'permissions-de-2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(self._translation_exists(title='permissions-de-2'))

    def test_user_cant_edit_title_fields(self):
        """
        User can't edit title (translation) fields if he does not have
        global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        title = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'edit_title_fields', page.pk, title.language)

        self.add_page_permission(
            staff_user,
            page,
            can_change=False,
        )
        self.add_permission(staff_user, 'change_page')

        with self.login_user_context(staff_user):
            data = model_to_dict(title, fields=['title'])
            data['title'] = 'permissions-de-2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._translation_exists(title='permissions-de-2'))

    # Plugin related tests

    def test_user_can_add_plugin(self):
        """
        User can add a plugin if he has change permissions
        on the Page model, add permissions on the plugin model
        and global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.placeholders.get(slot='body')
        plugins = placeholder.get_plugins('en').filter(plugin_type='LinkPlugin')
        endpoint = self._get_add_plugin_uri(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

        with self.login_user_context(staff_user):
            data = {'name': 'A Link', 'url': 'https://www.django-cms.org'}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(plugins.count(), 1)

    def test_user_cant_add_plugin(self):
        """
        User can't add a plugin if he
        does not have change permissions on the Page model,
        does not have add permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.placeholders.get(slot='body')
        plugins = placeholder.get_plugins('en').filter(plugin_type='LinkPlugin')
        endpoint = self._get_add_plugin_uri(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=False,
        )

        with self.login_user_context(staff_user):
            data = {'name': 'A Link', 'url': 'https://www.django-cms.org'}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(plugins.count(), 0)

    def test_user_can_edit_plugin(self):
        """
        User can edit a plugin if he has change permissions
        on the Page model, change permissions on the plugin model
        and global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_change_plugin_uri(plugin)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['name', 'url'])
            data['name'] = 'A link 2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            plugin.refresh_from_db()
            self.assertEqual(plugin.name, data['name'])

    def test_user_cant_edit_plugin(self):
        """
        User can't edit a plugin if he
        does not have change permissions on the Page model,
        does not have change permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_change_plugin_uri(plugin)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=False,
        )

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['name', 'url'])
            data['name'] = 'A link 2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            plugin.refresh_from_db()
            self.assertNotEqual(plugin.name, data['name'])

    def test_user_can_delete_plugin(self):
        """
        User can delete a plugin if he has change permissions
        on the Page model, delete permissions on the plugin model
        and global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_delete_plugin_uri(plugin)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

        with self.login_user_context(staff_user):
            data = {'post': True}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertFalse(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_user_cant_delete_plugin(self):
        """
        User can't delete a plugin if he
        does not have change permissions on the Page model,
        does not have delete permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_delete_plugin_uri(plugin)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=False,
        )

        with self.login_user_context(staff_user):
            data = {'post': True}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_user_can_move_plugin(self):
        """
        User can move a plugin if he has change permissions
        on the Page model, change permissions on the plugin model
        and global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_move_plugin_uri(plugin)
        source_placeholder = plugin.placeholder
        target_placeholder = page.placeholders.get(slot='right-column')

        data = {
            'plugin_id': plugin.pk,
            'placeholder_id': target_placeholder.pk,
            'plugin_parent': '',
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
            self.assertFalse(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

    def test_user_cant_move_plugin(self):
        """
        User can't move a plugin if he
        does not have change permissions on the Page model,
        does not have change permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_move_plugin_uri(plugin)
        source_placeholder = plugin.placeholder
        target_placeholder = page.placeholders.get(slot='right-column')

        data = {
            'plugin_id': plugin.pk,
            'placeholder_id': target_placeholder.pk,
            'plugin_parent': '',
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

    def test_user_can_copy_plugin(self):
        """
        User can copy a plugin if he has change permissions
        on the Page model, add permissions on the plugin model
        and global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        translation = self._add_translation_to_page(page)
        endpoint = self.get_copy_plugin_uri(plugin)
        source_placeholder = plugin.placeholder
        target_placeholder = page.placeholders.get(slot='right-column')

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': source_placeholder.pk,
            'source_language': plugin.language,
            'target_language': translation.language,
            'target_placeholder_id': target_placeholder.pk,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk).exists())
            self.assertTrue(
                target_placeholder
                .get_plugins(translation.language)
                .filter(plugin_type=plugin.plugin_type)
                .exists()
            )

    def test_user_cant_copy_plugin(self):
        """
        User can't copy a plugin if he
        does not have change permissions on the Page model,
        does not have add permissions on the plugin model,
        and/or does not have global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        translation = self._add_translation_to_page(page)
        endpoint = self.get_copy_plugin_uri(plugin)
        source_placeholder = plugin.placeholder
        target_placeholder = page.placeholders.get(slot='right-column')

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': source_placeholder.pk,
            'source_language': plugin.language,
            'target_language': translation.language,
            'target_placeholder_id': target_placeholder.pk,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk).exists())
            self.assertFalse(
                target_placeholder
                .get_plugins(translation.language)
                .filter(plugin_type=plugin.plugin_type)
                .exists()
            )

    def test_user_can_copy_plugins_to_language(self):
        """
        User can copy all plugins to another language if he has
        change permissions on the Page model, add permissions on the
        plugins being copied and global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'copy_language', page.pk)
        plugins = [
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
        ]
        placeholder = plugins[0].placeholder

        data = {
            'source_language': 'en',
            'target_language': translation.language,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            new_plugins = placeholder.get_plugins(translation.language)
            self.assertEqual(new_plugins.count(), len(plugins))

    def test_user_cant_copy_plugins_to_language(self):
        """
        User can't copy all plugins to another language if he does have
        change permissions on the Page model, does not have add permissions
        on the plugins being copied and/or does not have global
        change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(Page, 'copy_language', page.pk)
        plugins = [
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
        ]
        placeholder = plugins[0].placeholder

        data = {
            'source_language': 'en',
            'target_language': translation.language,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_page_permission(
            staff_user,
            page,
            can_change=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            new_plugins = placeholder.get_plugins(translation.language)
            self.assertEqual(new_plugins.count(), 0)

    # Placeholder related tests

    def test_user_can_clear_empty_placeholder(self):
        """
        User can clear an empty placeholder if he has change permissions
        on the Page model and global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.placeholders.get(slot='body')
        endpoint = self.get_clear_placeholder_url(placeholder)

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 302)

    def test_user_cant_clear_empty_placeholder(self):
        """
        User can't clear an empty placeholder if he does not have
        change permissions on the Page model and/or does not have
        global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.placeholders.get(slot='body')
        endpoint = self.get_clear_placeholder_url(placeholder)

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 403)

    def test_user_can_clear_non_empty_placeholder(self):
        """
        User can clear a placeholder with plugins if he has
        change permissions on the Page model, delete permissions
        on the plugin models in the placeholder and global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'LinkPlugin'),
        ]
        placeholder = plugins[0].placeholder
        endpoint = self.get_clear_placeholder_url(placeholder)

        self.add_permission(staff_user, 'delete_text')
        self.add_permission(staff_user, 'delete_link')
        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(placeholder.get_plugins('en').count(), 0)

    def test_user_cant_clear_non_empty_placeholder(self):
        """
        User can't clear a placeholder with plugins if he does not have
        change permissions on the Page model, does not have delete
        permissions on the plugin models in the placeholder and/or
        does not have global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'LinkPlugin'),
        ]
        placeholder = plugins[0].placeholder
        endpoint = self.get_clear_placeholder_url(placeholder)

        self.add_permission(staff_user, 'delete_text')
        self.add_permission(staff_user, 'delete_link')
        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 403)
            self.assertEqual(placeholder.get_plugins('en').count(), 2)


@override_settings(CMS_PERMISSION=False)
class PermissionsOffTest(PermissionsTestCase):
    """
    Tests all user interactions with the page admin
    while permissions are set to False.
    """


@override_settings(ROOT_URLCONF='cms.test_utils.project.noadmin_urls')
class NoAdminPageTests(CMSTestCase):

    def test_get_page_from_request_fakeadmin_nopage(self):
        noadmin_apps = [app for app in installed_apps() if app != 'django.contrib.admin']
        with self.settings(INSTALLED_APPS=noadmin_apps):
            request = self.get_request('/en/admin/')
            page = get_page_from_request(request)
            self.assertEqual(page, None)
