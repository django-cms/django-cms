import datetime
import json
import sys
from unittest import skipUnless

from django.conf import settings
from django.contrib import admin
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse
from django.test.html import HTMLParseError, Parser
from django.test.utils import override_settings
from django.urls import clear_url_caches
from django.utils.encoding import force_str
from django.utils.timezone import now as tz_now
from django.utils.translation import override as force_language

from cms import constants
from cms.admin.pageadmin import PageContentAdmin
from cms.api import add_plugin, create_page, create_page_content
from cms.appresolver import clear_app_resolvers
from cms.cache.permissions import get_permission_cache, set_permission_cache
from cms.middleware.user import CurrentUserMiddleware
from cms.models import PageContent
from cms.models.pagemodel import Page, PageUrl
from cms.models.permissionmodels import PagePermission
from cms.models.pluginmodel import CMSPlugin
from cms.test_utils.project.sampleapp.models import SampleAppConfig
from cms.test_utils.testcases import URL_CMS_PAGE_MOVE, CMSTestCase
from cms.test_utils.util.context_managers import (
    LanguageOverride,
    UserLoginContext,
)
from cms.toolbar.utils import get_object_edit_url
from cms.utils.compat import DJANGO_4_2
from cms.utils.compat.dj import installed_apps
from cms.utils.conf import get_cms_setting
from cms.utils.page import get_page_from_request
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
            'LinkPlugin': {'name': 'A Link', 'external_link': 'https://www.django-cms.org'},
        }
        placeholder = page.get_placeholders(language).get(slot='body')
        plugin = add_plugin(placeholder, plugin_type, language, **plugin_data[plugin_type])
        return plugin

    def _translation_exists(self, slug=None, title=None):
        if not slug:
            slug = 'permissions-de'

        lookup = PageContent.objects.filter(page__urls__slug=slug)

        if title:
            lookup = lookup.filter(title=title)
        return lookup.exists()

    def _get_add_plugin_uri(self, page, language='en'):
        placeholder = page.get_placeholders(language).get(slot='body')
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

    def _get_move_data(self, plugin, position, placeholder=None, parent=None):
        try:
            placeholder_id = placeholder.pk
        except AttributeError:
            placeholder_id = ''

        try:
            parent_id = parent.pk
        except AttributeError:
            parent_id = ''

        data = {
            'placeholder_id': placeholder_id,
            'target_language': 'en',
            'target_position': position,
            'plugin_id': plugin.pk,
            'plugin_parent': parent_id,
        }
        return data

    def get_page(self, parent=None, site=None,
                 language=None, template='nav_playground.html'):
        page_data = self.get_new_page_data_dbfields()
        return create_page(**page_data)

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
            response = self.client.get(self.get_page_add_uri('en'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<title>Add a page</title>', html=True)

    def test_create_page_admin(self):
        """
        Test that a page can be created via the admin
        """
        page_data = self.get_new_page_data()

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            self.assertEqual(PageContent.objects.all().count(), 0)
            self.assertEqual(Page.objects.all().count(), 0)
            # create home
            response = self.client.post(self.get_page_add_uri('en'), page_data)
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))

            page_url = PageUrl.objects.get(slug=page_data['slug'])
            self.assertEqual(page_url.page.get_title(), page_data['title'])
            self.assertEqual(page_url.page.get_slug('en'), page_data['slug'])
            self.assertEqual(page_url.page.get_placeholders('en').count(), 2)

    def test_create_page_with_unconfigured_language(self):
        """
        Test that a page can be created via the admin
        with the request language pointing to a language
        not configured for the current site
        """
        from django.contrib.auth import get_user_model
        from django.test import Client

        client = Client()
        superuser = self.get_superuser()
        Site.objects.create(id=2, name='example-2.com', domain='example-2.com')
        client.login(
            username=getattr(superuser, get_user_model().USERNAME_FIELD),
            password=getattr(superuser, get_user_model().USERNAME_FIELD),
        )
        self.assertEqual(PageContent.objects.all().count(), 0)
        self.assertEqual(Page.objects.all().count(), 0)
        # create home
        with self.settings(SITE_ID=2):
            endpoint = self.get_page_add_uri('en')
            # url uses "en" as the request language
            # but the site is configured to use "de" and "fr"
            response = client.post(endpoint, self.get_new_page_data())
            self.assertRedirects(response, self.get_pages_admin_list_uri('de'))
            self.assertEqual(Page.objects.filter(node__site=2).count(), 1)
            self.assertEqual(PageContent.objects.filter(language='de').count(), 1)

        # The user is on site #1 but switches sites using the site switcher
        # on the page changelist.
        client.post(self.get_pages_admin_list_uri(), {'site': 2})

        # url uses "en" as the request language
        # but the site is configured to use "de" and "fr"
        endpoint = self.get_page_add_uri('en')
        response = client.post(endpoint, self.get_new_page_data())
        self.assertRedirects(response, self.get_pages_admin_list_uri('de'))
        self.assertEqual(Page.objects.filter(node__site=2).count(), 2)
        self.assertEqual(PageContent.objects.filter(language='de').count(), 2)

        Site.objects.clear_cache()
        client.logout()

    def test_create_tree_admin(self):
        """
        Test that a tree can be created via the admin
        """
        page_1 = self.get_new_page_data()

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            # create home and auto publish
            response = self.client.post(self.get_page_add_uri('en'), page_1)
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))

            home_url = PageUrl.objects.get(slug=page_1['slug'])

            page_2 = self.get_new_page_data(parent_id=home_url.page.node.pk)
            page_3 = self.get_new_page_data(parent_id=home_url.page.node.pk)
            page_4 = self.get_new_page_data(parent_id=home_url.page.node.pk)

            response = self.client.post(self.get_page_add_uri('en'), page_2)
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))
            response = self.client.post(self.get_page_add_uri('en'), page_3)
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))

            page2_url = PageUrl.objects.get(slug=page_2['slug'])

            add_endpoint = self.get_page_add_uri('en')
            response = self.client.post(add_endpoint + '&target=%s&amp;position=right' % page2_url.page.pk, page_4)
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))

    def test_slug_collision(self):
        """
        Test a slug collision
        """
        page_data = self.get_new_page_data()
        # create first page
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            add_endpoint = self.get_page_add_uri('en')
            # Home
            response = self.client.post(add_endpoint, page_data)
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))
            # Second root
            response = self.client.post(add_endpoint, page_data)
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))

            response = self.client.post(add_endpoint, page_data)
            new_page = Page.objects.only('id').latest('id')
            expected_error = (
                '<ul class="errorlist"><li>Page '
                '<a href="{}" target="_blank">test page 1</a> '
                'has the same url \'test-page-1\' as current page.</li></ul>'
            ).format(self.get_page_change_uri('en', new_page))

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_error)

    def test_child_slug_collision(self):
        """
        Test a slug collision
        """
        root = create_page("home", 'nav_playground.html', "en")
        page = create_page("page", 'nav_playground.html', "en")
        sub_page = create_page("subpage", 'nav_playground.html', "en", parent=page)
        child_page = create_page("child-page", 'nav_playground.html', "en", parent=root)
        root.set_as_homepage()
        superuser = self.get_superuser()
        add_endpoint = self.get_page_add_uri('en')
        with self.login_user_context(superuser):
            # slug collision between two child pages of the same node
            page_data = self.get_new_page_data(page.node.pk)
            page_data['slug'] = 'subpage'
            response = self.client.post(add_endpoint, page_data)
            expected_markup = (
                '<ul class="errorlist">'
                '<li>Page <a href="{}" target="_blank">subpage</a> '
                'has the same url \'page/subpage\' as current page.</li></ul>'
            ).format(self.get_page_change_uri('en', sub_page))

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_markup)

            # slug collision between page with no parent and a child page of home-page
            page_data = self.get_new_page_data()
            page_data['slug'] = 'child-page'
            response = self.client.post(add_endpoint, page_data)
            expected_markup = (
                '<ul class="errorlist">'
                '<li>Page <a href="{}" target="_blank">child-page</a> '
                'has the same url \'child-page\' as current page.</li></ul>'
            ).format(self.get_page_change_uri('en', child_page))

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_markup)

            # slug collision between two top-level pages
            page_data = self.get_new_page_data()
            page_data['slug'] = 'page'
            response = self.client.post(add_endpoint, page_data)
            expected_markup = (
                '<ul class="errorlist">'
                '<li>Page <a href="{}" target="_blank">page</a> '
                'has the same url \'page\' as current page.</li></ul>'
            ).format(self.get_page_change_uri('en', page))

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_markup)

    def test_edit_page(self):
        """
        Test that a page can edited via the admin
        """
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            endpoint = self.get_page_add_uri('en')
            self.client.post(endpoint, page_data)
            page = Page.objects.get(urls__slug=page_data['slug'])
            response = self.client.get(self.get_page_change_uri('en', page))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<title>Change a page</title>', html=True)
            page_data['title'] = 'changed title'
            page_data['template'] = page.get_template('en')
            response = self.client.post(self.get_page_change_uri('en', page), page_data)
            page._clear_internal_cache()
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))
            self.assertEqual(page.get_title(), 'changed title')

    def test_page_redirect_field_validation(self):
        superuser = self.get_superuser()
        data = self.get_new_page_data()

        with self.login_user_context(superuser):
            self.client.post(self.get_page_add_uri('en'), data)

        page = Page.objects.get(urls__slug=data['slug'])
        data['template'] = page.template
        endpoint = self.get_page_change_uri('en', page)
        redirect_to = self.get_pages_admin_list_uri('en')

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

    def test_meta_description_fields_from_admin(self):
        """
        Test that description and keywords tags can be set via the admin
        """
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            page_data["meta_description"] = "I am a page"
            self.client.post(self.get_page_add_uri('en'), page_data)
            page = Page.objects.get(urls__slug=page_data['slug'])
            response = self.client.get(self.get_page_change_uri('en', page))
            self.assertEqual(response.status_code, 200)
            page_data['template'] = page.get_template('en')
            page_data['meta_description'] = 'I am a duck'
            response = self.client.post(self.get_page_change_uri('en', page), page_data)
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))
            page = Page.objects.get(urls__slug=page_data["slug"])
            self.assertEqual(page.get_meta_description(), 'I am a duck')

    def test_meta_description_from_template_tags(self):
        from django import template

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            page_data["title"] = "Hello"
            page_data["meta_description"] = "I am a page"
            self.client.post(self.get_page_add_uri('en'), page_data)
            page = Page.objects.get(urls__slug=page_data['slug'])
            self.client.post(self.get_page_change_uri('en', page), page_data)
            t = template.Template(
                "{% load cms_tags %}{% page_attribute title %} {% page_attribute meta_description %}")
            req = HttpRequest()
            page.save()
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
            before_change = tz_now() + datetime.timedelta(seconds=-1)
            self.client.post(self.get_page_add_uri('en'), page_data)
            page = Page.objects.get(urls__slug=page_data['slug'])
            self.client.post(self.get_page_change_uri('en', page), page_data)
            t = template.Template(
                "{% load cms_tags %}{% page_attribute changed_by %} changed "
                "on {% page_attribute changed_date as page_change %}"
                "{{ page_change|date:'Y-m-d\\TH:i:s' }}"
            )
            req = HttpRequest()
            page.save()
            after_change = tz_now()
            req.current_page = page
            req.GET = {}

            actual_result = t.render(template.Context({"request": req}))
            desired_result = f"{change_user} changed on {actual_result[-19:]}"
            save_time = datetime.datetime.strptime(
                actual_result[-19:],
                "%Y-%m-%dT%H:%M:%S"
            )

            self.assertEqual(actual_result, desired_result)
            # direct time comparisons are flaky, so we just check if the
            # page's changed_date is within the time range taken by this test
            self.assertLessEqual(before_change, save_time)
            self.assertLessEqual(save_time, after_change)

    def test_delete_page_confirmation(self):
        superuser = self.get_superuser()
        page_a = create_page("page_a", "nav_playground.html", "en")
        create_page("page_a_a", "nav_playground.html", "en", parent=page_a)
        page_a_b = create_page("page_a_b", "nav_playground.html", "en", parent=page_a)
        create_page("page_a_b_a", "nav_playground.html", "en", parent=page_a_b)
        endpoint = self.get_admin_url(Page, 'delete', page_a.pk)

        page_tree = [page_a] + list(page_a.get_descendant_pages())
        row_markup = '<a href="%s">%s</a>'

        with self.login_user_context(superuser):
            response = self.client.get(endpoint)
            for page in page_tree:
                content = page.get_content_obj('en')
                edit_url = self.get_admin_url(PageContent, 'change', content.pk)
                page_markup = row_markup % (edit_url, str(content))
                self.assertContains(response, page_markup, html=True)

    def test_homepage_with_children(self):
        homepage = create_page("home", "nav_playground.html", "en")
        homepage.set_as_homepage()
        pending_child_1 = create_page(
            "child-1",
            "nav_playground.html",
            language="en",
            parent=homepage,
        )
        pending_child_2 = create_page(
            "child-2",
            "nav_playground.html",
            language="en",
            parent=homepage,
        )
        expected_tree = [
            (homepage, ''),
            (pending_child_1, 'child-1'),
            (pending_child_2, 'child-2'),
        ]

        for page, url_path in expected_tree:
            page._clear_internal_cache()
            self.assertEqual(page.get_path('en'), url_path)

    def test_copy_page(self):
        """
        Test that a page can be copied via the admin
        """
        page_a = create_page("page_a", "nav_playground.html", "en")
        page_a_a = create_page("page_a_a", "nav_playground.html", "en",
                               parent=page_a, reverse_id="hello")
        create_page("page_a_a_a", "nav_playground.html", "en", parent=page_a_a)

        page_b = create_page("page_b", "nav_playground.html", "en")
        page_b_a = create_page("page_b_b", "nav_playground.html", "en",
                               parent=page_b)

        count = Page.objects.count()

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            self.copy_page(page_a, page_b_a)

        self.assertEqual(Page.objects.count() - count, 3)

    def test_copy_page_under_home(self):
        """
        Users should be able to copy a page and paste under the home page.
        """
        homepage = create_page("home", "nav_playground.html", "en")
        homepage.set_as_homepage()

        root_page_a = create_page("root-a", "nav_playground.html", "en")

        with self.login_user_context(self.get_superuser()):
            self.copy_page(root_page_a, homepage)

    def test_copy_page_with_plugins(self):
        """
        Copying a page with plugins should copy all plugins for the translation
        being copied into the respective translation in the new page.
        """
        cms_page = create_page("page_a_en", "nav_playground.html", "en")
        placeholder = cms_page.get_placeholders('en').get(slot='body')
        add_plugin(
            placeholder,
            plugin_type='LinkPlugin',
            language='en',
            name='Link {}'.format('en'),
            external_link='https://www.django-cms.org',
        )

        with self.login_user_context(self.get_superuser()):
            new_page = self.copy_page(cms_page, cms_page, position=1)
            new_placeholder = new_page.get_placeholders('en').get(slot='body')
        self.assertTrue(new_placeholder.get_plugins('en').exists())
        plugin = new_placeholder.get_plugins('en')[0].get_bound_plugin()
        self.assertEqual(plugin.name, 'Link en')

    def test_copy_page_to_root(self):
        """
        When a page is copied and its slug matches that of another page,
        add "-copy-2" at the end.
        """
        data = {
            'position': 2,
            'source_site': 1,
            'copy_permissions': 'on',
            'copy_moderation': 'on',
        }
        superuser = self.get_superuser()
        cms_page = create_page("page_a", "nav_playground.html", "en")

        with self.login_user_context(superuser):
            endpoint = self.get_admin_url(Page, 'copy_page', cms_page.pk)
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

        new_slug = cms_page.get_path('en') + '-copy-2'
        new_path = cms_page.get_slug('en') + '-copy-2'

        self.assertEqual(
            PageUrl.objects.filter(slug=new_slug, path=new_path).count(),
            1,
        )

    def test_copy_page_to_different_site(self):
        superuser = self.get_superuser()
        site_2 = Site.objects.create(id=2, domain='example-2.com', name='example-2.com')
        site_1_root = create_page("site 1 root", "nav_playground.html", "de")
        site_2_parent = create_page("parent", "nav_playground.html", "de", site=site_2)
        child_0002 = create_page(
            "child-0002",
            template="nav_playground.html",
            language="de",
            parent=site_2_parent,
            site=site_2,
        )
        child_0003 = create_page(
            "child-0003",
            template="nav_playground.html",
            language="de",
            parent=site_2_parent,
            site=site_2,
        )
        child_0005 = create_page(
            "child-0005",
            template="nav_playground.html",
            language="de",
            parent=site_2_parent,
            site=site_2,
        )

        with self.login_user_context(superuser):
            # Copy the root page from site 1 and insert it as first child
            # of the site 2 parent.
            child_0001 = self.copy_page(site_1_root, site_2_parent, position=0)

        with self.login_user_context(superuser):
            # Copy the root page from site 1 and insert it as fourth child
            # of the site 2 parent.
            child_0004 = self.copy_page(site_1_root, site_2_parent, position=3)

        tree = (
            (site_2_parent, '0002'),
            (child_0001, '00020001'),
            (child_0002, '00020002'),
            (child_0003, '00020003'),
            (child_0004, '00020004'),
            (child_0005, '00020005'),
        )

        for page, path in tree:
            node = self.reload(page.node)
            self.assertEqual(node.path, path)
            self.assertEqual(node.site_id, 2)

    def test_copy_page_to_different_site_fails_with_untranslated_page(self):
        data = {
            'position': 0,
            'source_site': 1,
            'copy_permissions': 'on',
            'copy_moderation': 'on',
        }
        superuser = self.get_superuser()
        site_2 = Site.objects.create(id=2, domain='example-2.com', name='example-2.com')
        site_1_root = create_page("site 1 root", "nav_playground.html", "en")
        expected_response = {
            "status": 400,
            "content": "Error! The page you're pasting is not translated in "
                       "any of the languages configured by the target site.",
        }

        with self.settings(SITE_ID=2):
            with self.login_user_context(superuser):
                # Simulate the copy-dialog
                endpoint = self.get_admin_url(Page, 'get_copy_dialog', site_1_root.pk)
                endpoint += '?source_site=%s' % site_1_root.node.site_id
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)

                # Copy the root page from site 1 and insert it as the first root page
                # on site 2.
                endpoint = self.get_admin_url(Page, 'copy_page', site_1_root.pk)
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)
                self.assertObjectDoesNotExist(Page.objects.all(), node__site=site_2)
                self.assertEqual(
                    json.loads(response.content.decode('utf8')),
                    expected_response,
                )

    def test_copy_page_to_different_site_with_no_pages(self):
        data = {
            'position': 0,
            'source_site': 1,
            'copy_permissions': 'on',
            'copy_moderation': 'on',
        }
        superuser = self.get_superuser()
        site_2 = Site.objects.create(id=2, domain='example-2.com', name='example-2.com')
        site_1_root = create_page("site 1 root", "nav_playground.html", "de")

        with self.settings(SITE_ID=2):
            with self.login_user_context(superuser):
                # Simulate the copy-dialog
                endpoint = self.get_admin_url(Page, 'get_copy_dialog', site_1_root.pk)
                endpoint += '?source_site=%s' % site_1_root.node.site_id
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)

                # Copy the root page from site 1 and insert it as the first root page
                # on site 2.
                endpoint = self.get_admin_url(Page, 'copy_page', site_1_root.pk)
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

        site_2_root = self.assertObjectExist(Page.objects.all(), node__site=site_2)

        tree = (
            (site_1_root, '0001'),
            (site_2_root, '0002'),
        )

        for page, path in tree:
            self.assertEqual(self.reload(page.node).path, path)

    def test_copy_page_to_explicit_position(self):
        """
        User should be able to copy a single page and paste it
        in a specific location on another page tree.
        """
        superuser = self.get_superuser()
        parent = create_page("parent", "nav_playground.html", "en")
        child_0002 = create_page("child-0002", "nav_playground.html", "en", parent=parent)
        child_0003 = create_page("child-0003", "nav_playground.html", "en", parent=parent)
        child_0005 = create_page("child-0005", "nav_playground.html", "en", parent=parent)
        child_0004 = create_page("child-0004", "nav_playground.html", "en")

        with self.login_user_context(superuser):
            # Copy the 0005 page and insert it as first child of parent
            child_0001 = self.copy_page(child_0005, parent, position=0)

        with self.login_user_context(superuser):
            # Copy the 0004 page and insert it as fourth child of parent
            child_0004 = self.copy_page(child_0004, parent, position=3)

        tree = (
            (parent, '0001'),
            (child_0001, '00010001'),
            (child_0002, '00010002'),
            (child_0003, '00010003'),
            (child_0004, '00010004'),
            (child_0005, '00010005'),
        )

        for page, path in tree:
            self.assertEqual(self.reload(page.node).path, path)

    def test_copy_page_tree_to_explicit_position(self):
        """
        User should be able to copy a page with descendants and paste it
        in a specific location on another page tree.
        """
        superuser = self.get_superuser()
        parent = create_page("parent", "nav_playground.html", "en")
        child_0002 = create_page("child-0002", "nav_playground.html", "en", parent=parent)
        child_0003 = create_page("child-0003", "nav_playground.html", "en", parent=parent)
        child_0005 = create_page("child-0005", "nav_playground.html", "en", parent=parent)
        create_page("child-00050001", "nav_playground.html", "en", parent=child_0005)
        create_page("child-00050002", "nav_playground.html", "en", parent=child_0005)
        create_page("child-00050003", "nav_playground.html", "en", parent=child_0005)
        child_0004 = create_page("child-0004", "nav_playground.html", "en")
        create_page("child-00040001", "nav_playground.html", "en", parent=child_0004)
        create_page("child-00040002", "nav_playground.html", "en", parent=child_0004)
        create_page("child-00040003", "nav_playground.html", "en", parent=child_0004)

        with self.login_user_context(superuser):
            # Copy the 0005 page and insert it as first child of parent
            child_0001 = self.copy_page(child_0005, parent, position=0)
            child_pages = list(child_0001.get_child_pages())
            child_00010001 = child_pages[0]
            child_00010002 = child_pages[1]
            child_00010003 = child_pages[2]

        with self.login_user_context(superuser):
            # Copy the 0004 page and insert it as fourth child of parent
            child_0004 = self.copy_page(child_0004, parent, position=3)
            child_pages = list(child_0004.get_child_pages())
            child_00040001 = child_pages[0]
            child_00040002 = child_pages[1]
            child_00040003 = child_pages[2]

        tree = (
            (parent, '0001'),
            (child_0001, '00010001'),
            (child_00010001, '000100010001'),
            (child_00010002, '000100010002'),
            (child_00010003, '000100010003'),
            (child_0002, '00010002'),
            (child_0003, '00010003'),
            (child_0004, '00010004'),
            (child_00040001, '000100040001'),
            (child_00040002, '000100040002'),
            (child_00040003, '000100040003'),
            (child_0005, '00010005'),
        )

        for page, path in tree:
            self.assertEqual(self.reload(page.node).path, path)

    def test_copy_self_page(self):
        """
        Test that a page can be copied via the admin
        """
        page_a = create_page("page_a", "nav_playground.html", "en")
        page_b = create_page("page_b", "nav_playground.html", "en", parent=page_a)
        page_c = create_page("page_c", "nav_playground.html", "en", parent=page_b)
        with self.login_user_context(self.get_superuser()):
            self.copy_page(page_b, page_b, position=1)
        self.assertEqual(Page.objects.all().count(), 5)
        self.assertEqual(page_b.get_child_pages().count(), 2)
        page_d = page_b.get_child_pages()[1]
        page_e = page_d.get_child_pages()[0]
        self.assertEqual(page_d.node.path, '000100010002')
        self.assertEqual(page_e.node.path, '0001000100020001')
        page_e.delete()
        page_d.delete()
        with self.login_user_context(self.get_superuser()):
            self.copy_page(page_b, page_c)
        self.assertEqual(page_c.get_child_pages().count(), 1)
        self.assertEqual(page_b.get_child_pages().count(), 1)
        page_ids = list(page_c.get_descendant_pages().values_list('pk', flat=True))
        page_c.get_descendant_pages().delete()
        Page.objects.filter(pk__in=page_ids).delete()
        self.assertEqual(Page.objects.all().count(), 3)
        page_b = page_b.reload()
        page_c = page_c.reload()
        with self.login_user_context(self.get_superuser()):
            self.copy_page(page_b, page_c, position=0)

    def test_move_page(self):
        superuser = self.get_superuser()
        add_endpoint = self.get_page_add_uri('en')
        with self.login_user_context(superuser):
            page_home = self.get_new_page_data()
            self.client.post(add_endpoint, page_home)
            page_data1 = self.get_new_page_data()
            self.client.post(add_endpoint, page_data1)
            page_data2 = self.get_new_page_data()
            self.client.post(add_endpoint, page_data2)
            page_data3 = self.get_new_page_data()
            self.client.post(add_endpoint, page_data3)
            pages = list(Page.objects.order_by('node__path'))
            home = pages[0]
            page1 = pages[1]
            page2 = pages[2]
            page3 = pages[3]

            # move pages
            response = self.client.post(URL_CMS_PAGE_MOVE % page3.pk, {"target": page2.pk, "position": "0"})
            self.assertEqual(response.status_code, 200)

            page3 = Page.objects.get(pk=page3.pk)
            response = self.client.post(URL_CMS_PAGE_MOVE % page2.pk, {"target": page1.pk, "position": "0"})
            self.assertEqual(response.status_code, 200)
            # check page2 path and url
            page2 = Page.objects.get(pk=page2.pk)
            self.assertEqual(page2.get_path('en'), page_data1['slug'] + "/" + page_data2['slug'])
            self.assertEqual(
                page2.get_absolute_url(),
                self.get_pages_root() + page_data1['slug'] + "/" + page_data2['slug'] + "/"
            )
            # check page3 path and url
            page3 = Page.objects.get(pk=page3.pk)
            self.assertEqual(
                page3.get_path('en'), page_data1['slug'] + "/" + page_data2['slug'] + "/" + page_data3['slug']
            )
            self.assertEqual(
                page3.get_absolute_url(),
                self.get_pages_root() + page_data1['slug'] + "/" + page_data2['slug'] + "/" + page_data3['slug'] + "/"
            )

            # Remove home page
            home.delete()

            # Promote page1 to be the new homepage
            page1.set_as_homepage()
            self.assertEqual(page1.get_path('en'), '')
            # check that page2 and page3 url have changed
            page2 = Page.objects.get(pk=page2.pk)
            page3 = Page.objects.get(pk=page3.pk)
            # set page2 as root and check path of 1 and 3
            response = self.client.post(URL_CMS_PAGE_MOVE % page2.pk,
                                        {"position": "0"})
            self.assertEqual(response.status_code, 200)
            page1 = Page.objects.get(pk=page1.pk)
            self.assertEqual(page1.get_path('en'), '')
            page2 = Page.objects.get(pk=page2.pk)
            self.assertFalse(page2.is_home)
            self.assertEqual(page2.get_path('en'), page_data2['slug'])
            page3 = Page.objects.get(pk=page3.pk)
            self.assertEqual(page3.get_path('en'), page_data2['slug'] + "/" + page_data3['slug'])

    def test_user_cant_nest_home_page(self):
        """
        Users should not be able to move the home-page
        inside another node of the tree.
        """
        homepage = create_page("home", "nav_playground.html", "en")
        homepage.set_as_homepage()
        home_sibling_1 = create_page("root-1", "nav_playground.html", "en")

        payload = {'id': homepage.pk, 'position': 0, 'target': home_sibling_1}

        with self.login_user_context(self.get_superuser()):
            endpoint = self.get_admin_url(Page, 'move_page', homepage.pk)
            response = self.client.post(endpoint, payload)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json().get('status', 400), 400)

    def test_move_home_page(self):
        """
        Users should be able to move the home-page
        anywhere on the root of the tree.
        """
        homepage = create_page("home", "nav_playground.html", "en")
        homepage.set_as_homepage()
        home_child_1 = create_page(
            "child-1",
            "nav_playground.html",
            language="en",
            parent=homepage,
        )
        home_child_2 = create_page(
            "child-2",
            "nav_playground.html",
            language="en",
            parent=homepage,
        )
        home_sibling_1 = create_page("root-1", "nav_playground.html", "en")

        expected_tree = [
            # Sadly treebeard doesn't switch the paths
            (home_sibling_1, '0002', 'root-1'),
            (homepage, '0003', ''),
            (home_child_1, '00030001', 'child-1'),
            (home_child_2, '00030002', 'child-2'),
        ]

        with self.login_user_context(self.get_superuser()):
            # Moves the homepage to the second position in the tree
            data = {'id': homepage.pk, 'position': 1}
            endpoint = self.get_admin_url(Page, 'move_page', homepage.pk)
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

            for page, node_path, url_path in expected_tree:
                page._clear_internal_cache()
                self.assertEqual(page.node.path, node_path)
                self.assertEqual(page.get_path('en'), url_path)

    def test_move_page_integrity(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_home = self.get_new_page_data()
            self.client.post(self.get_page_add_uri('en'), page_home)

            # Create parent page
            page_root = create_page("Parent", 'col_three.html', "en")

            # Create child pages
            create_page(
                "Child 1",
                template=constants.TEMPLATE_INHERITANCE_MAGIC,
                language="en",
                parent=page_root,
            )

            create_page(
                "Child 2",
                template=constants.TEMPLATE_INHERITANCE_MAGIC,
                language="en",
                parent=page_root,
            )

            # Create two root pages that ware meant as child pages
            page_child_3 = create_page("Child 3", 'col_three.html', "en")
            page_child_4 = create_page("Child 4", 'col_three.html', "en")

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
            self.assertEqual(page_root.node.get_descendants().count(), 4)

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
            response = self.client.post(self.get_page_add_uri('en'), page_data)
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))
            page = Page.objects.get(urls__slug=page_data['slug'])
            with LanguageOverride(TESTLANG):
                self.assertEqual(page.get_title(), 'changed title')

    def test_get_page_from_request_cached(self):
        mock_page = 'hello world'
        request = self.get_request(
            admin_reverse('sampleapp_category_change', args=(1,))
        )
        request._current_page_cache = mock_page
        page = get_page_from_request(request)
        self.assertEqual(page, mock_page)

    @override_settings(CMS_PERMISSION=False)
    def test_set_overwrite_url(self):
        superuser = self.get_superuser()
        cms_page = create_page('page', 'nav_playground.html', 'en')
        translation = cms_page.get_content_obj('en', fallback=False)
        expected = (
            '<input id="id_overwrite_url" maxlength="255" '
            'value="new-url" name="overwrite_url" type="text" />'
        ) if DJANGO_4_2 else (
            '<input type="text" name="overwrite_url" value="new-url" '
            'maxlength="255" aria-describedby="id_overwrite_url_helptext" '
            'id="id_overwrite_url">'
        )
        changelist = self.get_pages_admin_list_uri()
        endpoint = self.get_page_change_uri('en', cms_page)

        with self.login_user_context(superuser):
            page_data = {
                'title': translation.title,
                'slug': cms_page.get_slug('en'),
                'overwrite_url': '/new-url/',
                'template': translation.template,
            }
            response = self.client.post(endpoint, page_data)
            self.assertRedirects(response, changelist)

        with self.login_user_context(superuser):
            response = self.client.get(endpoint)
            self.assertContains(response, expected, html=True)

    @override_settings(CMS_PERMISSION=False)
    def test_set_existing_overwrite_url(self):
        superuser = self.get_superuser()

        create_page('home', 'nav_playground.html', 'en')
        boo = create_page('boo', 'nav_playground.html', 'en')
        hoo = create_page('hoo', 'nav_playground.html', 'en')
        translation = hoo.get_content_obj('en', fallback=False)
        expected_error = (
            '<ul class="errorlist"><li>Page '
            '<a href="{}" target="_blank">boo</a> '
            'has the same url \'boo\' as current page "hoo".</li></ul>'
        ).format(self.get_page_change_uri('en', boo))

        with self.login_user_context(superuser):
            endpoint = self.get_page_change_uri('en', hoo)
            page_data = {
                'title': translation.title,
                'slug': hoo.get_slug('en'),
                'overwrite_url': '/boo/',
                'template': translation.template,
            }
            response = self.client.post(endpoint, page_data)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_error, html=True)

    @override_settings(CMS_PERMISSION=False)
    def test_remove_overwrite_url(self):
        superuser = self.get_superuser()
        cms_page = create_page(
            'page',
            'nav_playground.html',
            language='en',
            overwrite_url='/new-url/',
        )
        translation = cms_page.get_content_obj('en', fallback=False)
        expected = (
            '<input id="id_overwrite_url" maxlength="255" '
            'name="overwrite_url" type="text" />'
        ) if DJANGO_4_2 else (
            '<input type="text" name="overwrite_url" maxlength="255" '
            'aria-describedby="id_overwrite_url_helptext" id="id_overwrite_url">'
        )
        changelist = self.get_pages_admin_list_uri()
        endpoint = self.get_page_change_uri('en', cms_page)

        # control test
        self.assertTrue(cms_page.urls.filter(path='new-url').exists())

        with self.login_user_context(superuser):
            page_data = {
                'title': translation.title,
                'slug': cms_page.get_slug('en'),
                'overwrite_url': '',
                'template': translation.template,
            }
            response = self.client.post(endpoint, page_data)
            self.assertRedirects(response, changelist)

        with self.login_user_context(superuser):
            response = self.client.get(endpoint)
            self.assertContains(response, expected, html=True)

    @override_settings(CMS_PERMISSION=False)
    def test_advanced_settings_form_apphook(self):
        superuser = self.get_superuser()
        cms_page = create_page('app', 'nav_playground.html', 'en')
        cms_pages = Page.objects.filter(pk=cms_page.pk)
        redirect_to = self.get_pages_admin_list_uri()
        endpoint = self.get_admin_url(Page, 'advanced', cms_page.pk)
        page_data = {
            "reverse_id": "",
            "navigation_extenders": "",
            "application_urls": "SampleApp",
            "application_namespace": "sampleapp",
        }

        with self.login_user_context(superuser):
            # set the apphook
            response = self.client.post(endpoint, page_data)
            self.assertRedirects(response, redirect_to)
            self.assertEqual(
                cms_pages.filter(
                    application_urls='SampleApp',
                    application_namespace='sampleapp',
                ).count(),
                1,
            )

        with self.login_user_context(superuser):
            # remove the apphook
            page_data['application_urls'] = ''
            page_data['application_namespace'] = ''
            response = self.client.post(endpoint, page_data)
            self.assertRedirects(response, redirect_to)
            self.assertEqual(
                cms_pages.filter(
                    application_urls='',
                    application_namespace=None,
                ).count(),
                1,
            )

    @override_settings(
        CMS_APPHOOKS=[
            'cms.test_utils.project.sampleapp.cms_apps.SampleApp',
            'cms.test_utils.project.sampleapp.cms_apps.SampleAppWithConfig',
        ],
        CMS_PERMISSION=False,
    )
    def test_advanced_settings_form_apphook_config(self):
        clear_app_resolvers()
        clear_url_caches()

        if 'cms.test_utils.project.sampleapp.cms_apps' in sys.modules:
            del sys.modules['cms.test_utils.project.sampleapp.cms_apps']

        self.apphook_clear()

        superuser = self.get_superuser()
        app_config = SampleAppConfig.objects.create(namespace='sample')
        cms_page = create_page('app', 'nav_playground.html', 'en')
        cms_pages = Page.objects.filter(pk=cms_page.pk)
        redirect_to = self.get_pages_admin_list_uri()
        endpoint = self.get_admin_url(Page, 'advanced', cms_page.pk)
        page_data = {
            "reverse_id": "",
            "navigation_extenders": "",
            "application_urls": "SampleAppWithConfig",
            "application_configs": app_config.pk,
            "application_namespace": "sampleapp",
        }

        with self.login_user_context(superuser):
            # set the apphook config
            response = self.client.post(endpoint, page_data)
            self.assertRedirects(response, redirect_to)
            self.assertEqual(
                cms_pages.filter(
                    application_urls='SampleAppWithConfig',
                    application_namespace=app_config.namespace,
                ).count(),
                1,
            )

        with self.login_user_context(superuser):
            # change from apphook with config to normal apphook
            page_data['application_urls'] = 'SampleApp'
            page_data['application_namespace'] = 'sampleapp'
            response = self.client.post(endpoint, page_data)
            self.assertRedirects(response, redirect_to)
            self.assertEqual(
                cms_pages.filter(
                    application_urls='SampleApp',
                    application_namespace='sampleapp',
                ).count(),
                1,
            )

        with self.login_user_context(superuser):
            # set the apphook config again
            page_data['application_urls'] = 'SampleAppWithConfig'
            page_data['application_namespace'] = 'sampleapp'
            response = self.client.post(endpoint, page_data)
            self.assertRedirects(response, redirect_to)
            self.assertEqual(
                cms_pages.filter(
                    application_urls='SampleAppWithConfig',
                    application_namespace=app_config.namespace,
                ).count(),
                1,
            )

        with self.login_user_context(superuser):
            # change the apphook config to an invalid value
            expected_error = '<ul class="errorlist"><li>Invalid application config value</li></ul>'
            page_data['application_configs'] = '2'
            response = self.client.post(endpoint, page_data)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_error)
            self.assertEqual(
                cms_pages.filter(
                    application_urls='SampleAppWithConfig',
                    application_namespace=app_config.namespace,
                ).count(),
                1,
            )

        with self.login_user_context(superuser):
            # remove the apphook
            page_data['application_urls'] = ''
            page_data['application_namespace'] = ''
            response = self.client.post(endpoint, page_data)
            self.assertRedirects(response, redirect_to)
            self.assertEqual(
                cms_pages.filter(
                    application_urls='',
                    application_namespace=None,
                ).count(),
                1,
            )
        clear_app_resolvers()
        clear_url_caches()

        if 'cms.test_utils.project.sampleapp.cms_apps' in sys.modules:
            del sys.modules['cms.test_utils.project.sampleapp.cms_apps']
        self.apphook_clear()

    def test_advanced_settings_view_on_site(self):
        """Advanced Page Settings `View on Site` object tool links to the Page's current language
        content preview url"""
        from cms.toolbar.utils import get_object_preview_url
        superuser = self.get_superuser()
        cms_page = create_page('app', 'nav_playground.html', 'en')
        cms_page_content = cms_page.get_content_obj(language='en')
        endpoint = self.get_admin_url(Page, 'advanced', cms_page.pk)

        with self.login_user_context(superuser):
            response = self.client.get(endpoint)

        self.assertContains(response, get_object_preview_url(cms_page_content, language="en"))

    def test_form_url_page_change(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            content_admin = PageContentAdmin(PageContent, admin.site)
            page = self.get_page()
            content = self.get_pagecontent_obj(page, 'en')
            form_url = self.get_page_change_uri('en', page)
            # Middleware is needed to correctly setup the environment for the admin
            request = self.get_request()
            middleware = CurrentUserMiddleware(lambda req: HttpResponse(""))
            middleware(request)
            response = content_admin.change_view(
                request, str(content.pk),
                form_url=form_url,
            )
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
                if not isinstance(document.children[0], str):
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
                endpoint = self.get_admin_url(PageContent, 'get_tree')
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)
                parsed = self._parse_page_tree(response, parser_class=PageTreeOptionsParser)
                content = force_str(parsed)
                self.assertIn('(Shift-Klick für erweiterte Einstellungen)', content)

    def test_page_get_tree_endpoint_flat(self):
        superuser = self.get_superuser()
        endpoint = self.get_admin_url(PageContent, 'get_tree')

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
            content = force_str(parsed)
            self.assertIn(tree, content)
            self.assertNotIn('<li>\nBeta\n</li>', content)

    def test_page_get_tree_endpoint_nested(self):
        superuser = self.get_superuser()
        endpoint = self.get_admin_url(PageContent, 'get_tree')

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
            'openNodes[]': [alpha.node.pk, gamma.node.pk]
        }

        with self.login_user_context(superuser):
            response = self.client.get(endpoint, data=data)
            self.assertEqual(response.status_code, 200)
            parsed = self._parse_page_tree(response, parser_class=PageTreeLiParser)
            content = force_str(parsed)
            self.assertIn(tree, content)

    def test_page_changelist_search(self):
        superuser = self.get_superuser()
        endpoint = self.get_pages_admin_list_uri()

        create_page('Home', 'nav_playground.html', 'en')
        alpha = create_page('Alpha', 'nav_playground.html', 'en')
        create_page('Beta', 'nav_playground.html', 'en', parent=alpha)
        create_page('Gamma', 'nav_playground.html', 'en')

        with self.login_user_context(superuser):
            response = self.client.get(endpoint, data={'q': 'alpha'})
            self.assertEqual(response.status_code, 200)
            parsed = self._parse_page_tree(response, parser_class=PageTreeLiParser)
            content = force_str(parsed)
            self.assertIn('<li>\nAlpha\n</li>', content)
            self.assertNotIn('<li>\nHome\n</li>', content)
            self.assertNotIn('<li>\nBeta\n</li>', content)
            self.assertNotIn('<li>\nGamma\n</li>', content)

    def test_global_limit_on_plugin_move(self):
        superuser = self.get_superuser()
        cms_page = self.get_page()
        source_placeholder = cms_page.get_placeholders("en").get(slot='right-column')
        target_placeholder = cms_page.get_placeholders("en").get(slot='body')
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
                data = self._get_move_data(plugin_1, position=1, placeholder=target_placeholder)
                endpoint = self.get_move_plugin_uri(plugin_1)
                response = self.client.post(endpoint, data)  # first
                self.assertEqual(response.status_code, 200)
                data = self._get_move_data(plugin_2, position=2, placeholder=target_placeholder)
                endpoint = self.get_move_plugin_uri(plugin_2)
                response = self.client.post(endpoint, data)  # second
                self.assertEqual(response.status_code, 200)
                data = self._get_move_data(plugin_3, position=3, placeholder=target_placeholder)
                endpoint = self.get_move_plugin_uri(plugin_3)
                response = self.client.post(endpoint, data)  # third
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content, b"This placeholder already has the maximum number of plugins (2).")

    def test_type_limit_on_plugin_move(self):
        superuser = self.get_superuser()
        cms_page = self.get_page()
        source_placeholder = cms_page.get_placeholders("en").get(slot='right-column')
        target_placeholder = cms_page.get_placeholders("en").get(slot='body')
        data = {
            'placeholder': source_placeholder,
            'plugin_type': 'TextPlugin',
            'language': 'en',
        }
        plugin_1 = add_plugin(**data)
        plugin_2 = add_plugin(**data)
        with UserLoginContext(self, superuser):
            with self.settings(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                data = self._get_move_data(plugin_1, position=1, placeholder=target_placeholder)
                endpoint = self.get_move_plugin_uri(plugin_1)
                response = self.client.post(endpoint, data)  # first
                self.assertEqual(response.status_code, 200)
                data = self._get_move_data(plugin_2, position=2, placeholder=target_placeholder)
                endpoint = self.get_move_plugin_uri(plugin_1)
                response = self.client.post(endpoint, data)  # second
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content,
                                 b"This placeholder already has the maximum number (1) of allowed Text plugins.")

    @skipUnless(
        'sqlite' in settings.DATABASES.get('default').get('ENGINE').lower(),
        'This test only works in SQLITE',
    )
    @override_settings(USE_THOUSAND_SEPARATOR=True, USE_L10N=True)
    def test_page_tree_render_localized_page_ids(self):
        from django.db import connection

        # Artificially increment the sequence number on cms_page and cms_treenode (below)
        # to be > 1000, to trigger a THOUSAND_SEPARATOR localization in the
        # rendered template

        admin_user = self.get_superuser()
        root = create_page(
            "home", "nav_playground.html", "fr", created_by=admin_user,
        )
        with connection.cursor() as c:
            c.execute('UPDATE SQLITE_SEQUENCE SET seq = 1001 WHERE name="cms_page"')
            c.execute('UPDATE SQLITE_SEQUENCE SET seq = 1001 WHERE name="cms_treenode"')

        page = create_page(
            "child-page",
            "nav_playground.html",
            "fr",
            created_by=admin_user,
            parent=root,
            slug="child-page",
        )

        sub_page = create_page(
            "grand-child-page",
            "nav_playground.html",
            "fr",
            created_by=admin_user,
            parent=page,
            slug="grand-child-page",
        )
        self.assertTrue(page.id > 1000)
        self.assertTrue(sub_page.id > 1000)

        self.assertTrue(page.node.id > 1000)
        self.assertTrue(sub_page.node.id > 1000)

        # make sure the rendered page tree doesn't
        # localize page or node ids
        with self.login_user_context(admin_user):
            data = {'openNodes[]': [root.node.pk, page.node.pk], 'language': 'fr'}

            endpoint = self.get_admin_url(PageContent, 'get_tree')
            response = self.client.get(endpoint, data=data)

            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, f'parent_node={page.node.pk:,}')
            self.assertContains(response, f'parent_node={page.node.pk}')

        # if per chance we have localized node ids in our localstorage,
        # make sure DjangoCMS doesn't choke on them when they are passed
        # into the view
        with self.login_user_context(admin_user):
            data = {'openNodes[]': [root.node.pk, f'{page.node.pk:,}'], 'language': 'fr'}
            endpoint = self.get_admin_url(PageContent, 'get_tree')
            response = self.client.get(endpoint, data=data)
            self.assertEqual(response.status_code, 200)


class PageActionsTestCase(PageTestBase):
    def setUp(self):
        self.admin = self.get_superuser()
        self.site = Site.objects.get(pk=1)
        self.page = create_page(
            'My Page', 'nav_playground.html', 'en',
            slug="ok",
            site=self.site, created_by=self.admin)

    def test_add_page_redirect(self):
        """When adding the edit parameter to the add page form, the user should be redirected to the edit endpoint
        of the new page."""
        with self.login_user_context(self.admin):
            # add page
            page_data = {
                'title': 'another page', 'slug': 'type1', 'template': 'nav_playground.html',
                'language': 'en',
                'edit': 1,
            }
            self.assertEqual(Page.objects.all().count(), 1)
            response = self.client.post(
                self.get_admin_url(PageContent, 'add'),
                data=page_data,
            )
            redirect_url = get_object_edit_url(PageContent.objects.get(title='another page'))
            self.assertContains(response, f'href="{redirect_url}"')
            self.assertEqual(Page.objects.all().count(), 2)

    def test_add_page_no_redirect(self):
        with self.login_user_context(self.admin):
            # add page
            page_data = {
                'title': 'another page', 'slug': 'type1', 'template': 'nav_playground.html',
                'language': 'en',
                'edit': 0,
            }
            self.assertEqual(Page.objects.all().count(), 1)
            response = self.client.post(
                self.get_admin_url(PageContent, 'add'),
                data=page_data,
            )
            redirect_url = self.get_admin_url(PageContent, 'changelist') + "?language=en"
            self.assertRedirects(response, redirect_url)
            self.assertEqual(Page.objects.all().count(), 2)

class PermissionsTestCase(PageTestBase):

    def _add_translation_to_page(self, page):
        translation = create_page_content(
            "de",
            "permissions-de",
            page.reload(),
            slug="permissions-de",
            template="nav_playground.html",
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
                attr = f'pagepermission_set-2-0-{attr}'
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
                attr = f'pagepermission_set-0-{attr}'
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
                '<a href="/en/admin/cms/pagecontent/">Page contents</a>',
                html=True,
            )

        endpoint = self.get_pages_admin_list_uri()

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

        endpoint = self.get_pages_admin_list_uri()

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)

    def test_user_can_edit_page_settings(self):
        """
        User can edit page settings if he has change permissions
        on the Page model and and he has global change permissions.
        """
        page = self.get_permissions_test_page()
        endpoint = self.get_page_change_uri('en', page)
        redirect_to = self.get_pages_admin_list_uri()
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
        endpoint = self.get_page_change_uri('en', page)
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
        redirect_to = self.get_pages_admin_list_uri()
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
        redirect_to = self.get_pages_admin_list_uri()
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
        redirect_to = self.get_pages_admin_list_uri()
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
        self.remove_permission(staff_user, 'delete_page')
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
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'delete', translation.pk)
        redirect_to = self.get_pages_admin_list_uri()
        staff_user = self.get_staff_user_with_no_permissions()

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
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'delete', translation.pk)
        staff_user = self.get_staff_user_with_no_permissions()

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
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'delete', translation.pk)
        redirect_to = self.get_pages_admin_list_uri()
        staff_user = self.get_staff_user_with_no_permissions()

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
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'delete', translation.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        self._add_plugin_to_page(page, language=translation.language)

        self.add_permission(staff_user, 'change_page')
        self.remove_permission(staff_user, 'delete_page')
        self.add_global_permission(staff_user, can_change=True, can_delete=True)

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

    def test_user_can_change_template(self):
        """
        User can change a page's template if he
        has change permissions on the Page model and both
        global change and change advanced settings permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        endpoint = self.get_page_change_template_uri('en', page)

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True, can_change_advanced_settings=True)

        with self.login_user_context(staff_user):
            page._clear_internal_cache()
            data = {'template': 'simple.html'}
            response = self.client.post(endpoint, data)
            self.assertContains(response, 'The template was successfully changed')
            self.assertEqual(page.get_template(), 'simple.html')

    def test_user_cant_change_template(self):
        """
        User can't change a page's template if he
        does not have change permissions on the Page model,
        global change permissions and/or global change advanced settings
        permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        endpoint = self.get_page_change_template_uri('en', page)

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = {'template': 'simple.html'}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(page.get_template(), 'nav_playground.html')

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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
            self.assertTrue(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_permissions_cache_invalidation(self):
        """
        Test permission cache clearing on page save
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_std_permissions()
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
        set_permission_cache(staff_user, "change_page", [page.pk])

        with self.login_user_context(self.get_superuser()):
            data = self._get_page_permissions_data(page=page.pk, user=staff_user.pk)
            data['_continue'] = '1'
            self.client.post(endpoint, data)
        self.assertIsNone(get_permission_cache(staff_user, "change_page"))

    def test_user_can_copy_page(self):
        """
        Test that a page can be copied via the admin
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'add_page')
        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(
            staff_user,
            can_add=True,
            can_change=True,
        )

        count = Page.objects.count()

        with self.login_user_context(staff_user):
            endpoint = self.get_admin_url(Page, 'get_copy_dialog', page.pk)
            endpoint += '?source_site=%s' % page.node.site_id
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)

        with self.login_user_context(staff_user):
            self.copy_page(page, page, position=1)
        self.assertEqual(count + 1, 3)

    # Plugin related tests

    def test_user_can_add_plugin(self):
        """
        User can add a plugin if he has change permissions
        on the Page model, add permissions on the plugin model
        and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.get_placeholders("en").get(slot='body')
        plugins = placeholder.get_plugins('en').filter(plugin_type='LinkPlugin')
        endpoint = self._get_add_plugin_uri(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
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
        placeholder = page.get_placeholders("en").get(slot='body')
        plugins = placeholder.get_plugins('en').filter(plugin_type='LinkPlugin')
        endpoint = self._get_add_plugin_uri(page)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
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
            data = model_to_dict(plugin, fields=['name', 'external_link'])
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
            data = model_to_dict(plugin, fields=['name', 'external_link'])
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
        target_placeholder = page.get_placeholders('en').get(slot='right-column')

        data = self._get_move_data(plugin, position=1, placeholder=target_placeholder)

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
        target_placeholder = page.get_placeholders("en").get(slot='right-column')

        data = self._get_move_data(plugin, position=1, placeholder=target_placeholder)

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
        target_placeholder = page.get_placeholders('en').get(slot='right-column')

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
        target_placeholder = page.get_placeholders('en').get(slot='right-column')

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
        source_translation = self.get_pagecontent_obj(page, 'en')
        target_translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'copy_language', source_translation.pk)
        plugins = [
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
        ]
        source_placeholder = plugins[0].placeholder
        target_placeholder = target_translation.get_placeholders().get(slot=source_placeholder.slot)

        data = {
            'source_language': 'en',
            'target_language': target_translation.language,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            new_plugins = target_placeholder.get_plugins()
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
        endpoint = self.get_admin_url(PageContent, 'copy_language', translation.pk)
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
        placeholder = page.get_placeholders("en").get(slot='body')
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
        placeholder = page.get_placeholders("en").get(slot='body')
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
                '<a href="/en/admin/cms/pagecontent/">Page contents</a>',
                html=True,
            )

        endpoint = self.get_pages_admin_list_uri()

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

        endpoint = self.get_pages_admin_list_uri()

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)

    def test_user_can_edit_page_settings(self):
        """
        User can edit page settings if he has change permissions
        on the Page model and and he has global change permissions.
        """
        page = self._permissions_page
        endpoint = self.get_page_change_uri('en', page)
        redirect_to = self.get_pages_admin_list_uri()
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
        endpoint = self.get_page_change_uri('en', page)
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
        redirect_to = self.get_pages_admin_list_uri()
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

    def test_user_can_delete_empty_translation(self):
        """
        User can delete an empty translation if he has
        delete permissions on the Page model and he has
        page delete & change permissions.
        """
        page = self._permissions_page
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'delete', translation.pk)
        redirect_to = self.get_pages_admin_list_uri()
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
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'delete', translation.pk)
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
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'delete', translation.pk)
        redirect_to = self.get_pages_admin_list_uri()
        staff_user = self.get_staff_user_with_no_permissions()

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
        translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'delete', translation.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        self._add_plugin_to_page(page, language=translation.language)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_page')
        self.add_page_permission(
            staff_user,
            page,
            can_change=False,
            can_delete=True,
        )

        with self.login_user_context(staff_user):
            data = {'language': translation.language}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._translation_exists())

    def test_user_can_add_page_permissions(self):
        """
        User can add page permissions if he has
        change permissions on the Page model,
        add permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
            self.assertFalse(self._page_permission_exists(user=staff_user_2))

    def test_user_can_edit_page_permissions(self):
        """
        User can edit page permissions if he has
        change permissions on the Page model,
        change permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
            self.assertTrue(self._page_permission_exists(user=staff_user_2))

    def test_user_can_add_page_view_restrictions(self):
        """
        User can add page view restrictions if he has
        change permissions on the Page model,
        add permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
            self.assertFalse(self._page_permission_exists(user=staff_user_2, can_view=True))

    def test_user_can_edit_page_view_restrictions(self):
        """
        User can edit page view restrictions if he has
        change permissions on the Page model,
        change permissions on the PagePermission model,
        global change permission and global change permissions permission.
        """
        page = self._permissions_page
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertContains(response, '<h2>Page permissions</h2>', html=True)
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
        endpoint = self.get_admin_url(Page, 'advanced', page.pk) + '?language=en'
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
            can_change_advanced_settings=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertNotContains(response, '<h2>Page permissions</h2>', html=True)
            self.client.post(endpoint, data)
            self.assertTrue(self._page_permission_exists(user=staff_user_2, can_view=True))

    # Plugin related tests

    def test_user_can_add_plugin(self):
        """
        User can add a plugin if he has change permissions
        on the Page model, add permissions on the plugin model
        and global change permissions.
        """
        page = self._permissions_page
        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.get_placeholders("en").get(slot='body')
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
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
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
        placeholder = page.get_placeholders("en").get(slot='body')
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
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
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
            data = model_to_dict(plugin, fields=['name', 'external_link'])
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
            data = model_to_dict(plugin, fields=['name', 'external_link'])
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
        target_placeholder = page.get_placeholders('en').get(slot='right-column')

        data = self._get_move_data(plugin, position=1, placeholder=target_placeholder)

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
        target_placeholder = page.get_placeholders("en").get(slot='right-column')

        data = self._get_move_data(plugin, position=1, placeholder=target_placeholder)

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
        page.get_content_obj(translation.language)
        target_placeholder = page.get_placeholders(translation.language).get(slot='right-column')

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
        target_placeholder = page.get_placeholders(translation.language).get(slot='right-column')

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
        source_translation = self.get_pagecontent_obj(page, 'en')
        target_translation = self._add_translation_to_page(page)
        endpoint = self.get_admin_url(PageContent, 'copy_language', source_translation.pk)
        plugins = [
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
            self._add_plugin_to_page(page),
        ]
        source_placeholder = plugins[0].placeholder
        target_placeholder = target_translation.get_placeholders().get(slot=source_placeholder.slot)

        data = {
            'source_language': 'en',
            'target_language': target_translation.language,
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
            new_plugins = target_placeholder.get_plugins()
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
        endpoint = self.get_admin_url(PageContent, 'copy_language', translation.pk)
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
        placeholder = page.get_placeholders("en").get(slot='body')
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
        placeholder = page.get_placeholders("en").get(slot='body')
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
