# -*- coding: utf-8 -*-
import json

from djangocms_text_ckeditor.cms_plugins import TextPlugin
from djangocms_text_ckeditor.models import Text
from django.contrib import admin
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.urls import reverse
from django.http import (Http404, HttpResponseBadRequest,
                         HttpResponseNotFound)
from django.utils.encoding import force_text, smart_str

from cms import api
from cms.api import create_page, create_title, add_plugin
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import PageContent, StaticPlaceholder
from cms.models.pagemodel import Page, PageType
from cms.models.permissionmodels import GlobalPagePermission, PagePermission
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.test_utils import testcases as base
from cms.test_utils.testcases import (
    CMSTestCase, URL_CMS_PAGE_DELETE, URL_CMS_PAGE,URL_CMS_TRANSLATION_DELETE,
    URL_CMS_PAGE_CHANGE_LANGUAGE, URL_CMS_PAGE_CHANGE,
    URL_CMS_PAGE_PUBLISHED,
)
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse


class AdminTestsBase(CMSTestCase):
    @property
    def admin_class(self):
        return site._registry[Page]

    def _get_guys(self, admin_only=False, use_global_permissions=True):
        admin_user = self.get_superuser()

        if admin_only:
            return admin_user
        staff_user = self._get_staff_user(use_global_permissions)
        return admin_user, staff_user

    def _get_staff_user(self, use_global_permissions=True):
        USERNAME = 'test'

        if get_user_model().USERNAME_FIELD == 'email':
            normal_guy = get_user_model().objects.create_user(USERNAME, 'test@test.com', 'test@test.com')
        else:
            normal_guy = get_user_model().objects.create_user(USERNAME, 'test@test.com', USERNAME)

        normal_guy.is_staff = True
        normal_guy.is_active = True
        perms = Permission.objects.filter(
            codename__in=['change_page', 'change_title', 'add_page', 'add_title', 'delete_page', 'delete_title']
        )
        normal_guy.save()
        normal_guy.user_permissions.set(perms)
        if use_global_permissions:
            gpp = GlobalPagePermission.objects.create(
                user=normal_guy,
                can_change=True,
                can_delete=True,
                can_change_advanced_settings=False,
                can_publish=True,
                can_change_permissions=False,
                can_move_page=True,
            )
            gpp.sites.set(Site.objects.all())
        return normal_guy


class AdminTestCase(AdminTestsBase):

    def test_extension_not_in_admin(self):
        admin_user, staff = self._get_guys()
        with self.login_user_context(admin_user):
            request = self.get_request(URL_CMS_PAGE_CHANGE % 1, 'en',)
            response = site.index(request)
            self.assertNotContains(response, '/mytitleextension/')
            self.assertNotContains(response, '/mypageextension/')

    def test_2apphooks_with_same_namespace(self):
        PAGE1 = 'Test Page'
        PAGE2 = 'Test page 2'
        APPLICATION_URLS = 'project.sampleapp.urls'

        admin_user, normal_guy = self._get_guys()

        current_site = Site.objects.get(pk=1)

        # The admin creates the page
        page = create_page(PAGE1, "nav_playground.html", "en",
                           site=current_site, created_by=admin_user)
        page2 = create_page(PAGE2, "nav_playground.html", "en",
                            site=current_site, created_by=admin_user)

        page.application_urls = APPLICATION_URLS
        page.application_namespace = "space1"
        page.save()
        page2.application_urls = APPLICATION_URLS
        page2.save()

        # The admin edits the page (change the page name for ex.)
        page_data = {
            'title': PAGE2,
            'slug': page2.get_slug('en'),
            'template': page2.template,
            'application_urls': 'SampleApp',
            'application_namespace': 'space1',
        }

        with self.login_user_context(admin_user):
            resp = self.client.post(base.URL_CMS_PAGE_ADVANCED_CHANGE % page.pk, page_data)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(Page.objects.filter(application_namespace="space1").count(), 1)
            resp = self.client.post(base.URL_CMS_PAGE_ADVANCED_CHANGE % page2.pk, page_data)
            self.assertEqual(resp.status_code, 200)
            page_data['application_namespace'] = 'space2'
            resp = self.client.post(base.URL_CMS_PAGE_ADVANCED_CHANGE % page2.pk, page_data)
            self.assertEqual(resp.status_code, 302)

    def test_delete(self):
        admin_user = self.get_superuser()
        create_page("home", "nav_playground.html", "en",
                           created_by=admin_user)
        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user)
        create_page('child-page', "nav_playground.html", "en",
                    created_by=admin_user, parent=page)
        body = page.get_placeholders("en").get(slot='body')
        add_plugin(body, 'TextPlugin', 'en', body='text')
        with self.login_user_context(admin_user):
            data = {'post': 'yes'}
            response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)
            self.assertRedirects(response, URL_CMS_PAGE)

    def test_delete_diff_language(self):
        admin_user = self.get_superuser()
        create_page("home", "nav_playground.html", "en",
                           created_by=admin_user)
        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user)
        create_page('child-page', "nav_playground.html", "de",
                    created_by=admin_user, parent=page)
        body = page.get_placeholders("en").get(slot='body')
        add_plugin(body, 'TextPlugin', 'en', body='text')
        with self.login_user_context(admin_user):
            data = {'post': 'yes'}
            response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)
            self.assertRedirects(response, URL_CMS_PAGE)

    def test_search_fields(self):
        superuser = self.get_superuser()
        from django.contrib.admin import site

        with self.login_user_context(superuser):
            for model, admin_instance in site._registry.items():
                if model._meta.app_label != 'cms':
                    continue
                if not admin_instance.search_fields:
                    continue
                url = admin_reverse('cms_%s_changelist' % model._meta.model_name)
                response = self.client.get('%s?q=1' % url)
                errmsg = response.content
                self.assertEqual(response.status_code, 200, errmsg)

    def test_pagetree_filtered(self):
        superuser = self.get_superuser()
        create_page("root-page", "nav_playground.html", "en",
                    created_by=superuser)
        with self.login_user_context(superuser):
            url = admin_reverse('cms_page_changelist')
            response = self.client.get('%s?template__exact=nav_playground.html' % url)
            errmsg = response.content
            self.assertEqual(response.status_code, 200, errmsg)

    def test_delete_translation(self):
        admin_user = self.get_superuser()
        page = create_page("delete-page-translation", "nav_playground.html", "en",
                           created_by=admin_user)
        create_title("de", "delete-page-translation-2", page, slug="delete-page-translation-2")
        create_title("es-mx", "delete-page-translation-es", page, slug="delete-page-translation-es")
        with self.login_user_context(admin_user):
            response = self.client.get(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'de'})
            self.assertEqual(response.status_code, 200)
            response = self.client.post(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'de'})
            self.assertRedirects(response, URL_CMS_PAGE)
            response = self.client.get(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'es-mx'})
            self.assertEqual(response.status_code, 200)
            response = self.client.post(URL_CMS_TRANSLATION_DELETE % page.pk, {'language': 'es-mx'})
            self.assertRedirects(response, URL_CMS_PAGE)

    def test_change_template(self):
        template = get_cms_setting('TEMPLATES')[0][0]
        admin_user, staff = (self.get_superuser(), self.get_staff_user_with_no_permissions())

        with self.login_user_context(admin_user):
            response = self.client.post(
                self.get_admin_url(Page, 'change_template', 1),
                {'template': template}
            )
            self.assertEqual(response.status_code, 404)

        with self.login_user_context(staff):
            response = self.client.post(
                self.get_admin_url(Page, 'change_template', 1),
                {'template': template}
            )
            self.assertEqual(response.status_code, 403)

        page = create_page('test-page', template, 'en')

        with self.login_user_context(staff):
            response = self.client.post(
                self.get_admin_url(Page, 'change_template', page.pk),
                {'template': template}
            )
            self.assertEqual(response.status_code, 403)

        with self.login_user_context(admin_user):
            response = self.client.post(
                self.get_admin_url(Page, 'change_template', page.pk),
                {'template': 'doesntexist'}
            )
            self.assertEqual(response.status_code, 400)
            response = self.client.post(
                self.get_admin_url(Page, 'change_template', page.pk),
                {'template': template}
            )
            self.assertEqual(response.status_code, 200)

    def test_changelist_items(self):
        admin_user = self.get_superuser()
        first_level_page = create_page('level1', 'nav_playground.html', 'en')
        second_level_page_top = create_page('level21', "nav_playground.html", "en",
                                            created_by=admin_user, parent=first_level_page)
        second_level_page_bottom = create_page('level22', "nav_playground.html", "en",
                                               created_by=admin_user,
                                               parent=self.reload(first_level_page))
        third_level_page = create_page('level3', "nav_playground.html", "en",
                                       created_by=admin_user, parent=second_level_page_top)
        self.assertEqual(Page.objects.all().count(), 4)

        with self.login_user_context(admin_user):
            response = self.client.get(self.get_admin_url(Page, 'changelist'))
            cms_page_nodes = response.context_data['tree']['items']
            self.assertEqual(cms_page_nodes[0], first_level_page)
            self.assertEqual(cms_page_nodes[1], second_level_page_top)
            self.assertEqual(cms_page_nodes[2], third_level_page)
            self.assertEqual(cms_page_nodes[3], second_level_page_bottom)

    def test_changelist_get_results(self):
        admin_user = self.get_superuser()
        first_level_page = create_page('level1', 'nav_playground.html', 'en')
        second_level_page_top = create_page('level21', "nav_playground.html", "en",
                                            created_by=admin_user,
                                            parent=first_level_page)
        second_level_page_bottom = create_page('level22', "nav_playground.html", "en", # nopyflakes
                                               created_by=admin_user,
                                               parent=self.reload(first_level_page))
        third_level_page = create_page('level3', "nav_playground.html", "en", # nopyflakes
                                       created_by=admin_user,
                                       parent=second_level_page_top)
        fourth_level_page = create_page('level23', "nav_playground.html", "en", # nopyflakes
                                        created_by=admin_user,
                                        parent=self.reload(first_level_page))
        self.assertEqual(Page.objects.all().count(), 5)
        endpoint = self.get_admin_url(Page, 'changelist')

        with self.login_user_context(admin_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.context_data['tree']['items'].count(), 5)

        with self.login_user_context(admin_user):
            response = self.client.get(endpoint + '?q=level23')
            self.assertEqual(response.context_data['tree']['items'].count(), 1)

        with self.login_user_context(admin_user):
            response = self.client.get(endpoint + '?q=level2')
            self.assertEqual(response.context_data['tree']['items'].count(), 3)

    def test_unihandecode_doesnt_break_404_in_admin(self):
        self.get_superuser()

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='admin@django-cms.org', password='admin@django-cms.org')
        else:
            self.client.login(username='admin', password='admin')

        response = self.client.get(URL_CMS_PAGE_CHANGE_LANGUAGE % (1, 'en'))
        self.assertEqual(response.status_code, 404)

    def test_empty_placeholder_with_nested_plugins(self):
        # It's important that this test clears a placeholder
        # which only has nested plugins.
        # This allows us to catch a strange bug that happened
        # under these conditions with the new related name handling.
        page_en = create_page("EmptyPlaceholderTestPage (EN)", "nav_playground.html", "en")
        ph = page_en.get_placeholders("en").get(slot="body")

        column_wrapper = add_plugin(ph, "MultiColumnPlugin", "en")

        add_plugin(ph, "ColumnPlugin", "en", parent=column_wrapper)
        add_plugin(ph, "ColumnPlugin", "en", parent=column_wrapper)

        # before cleaning the de placeholder
        self.assertEqual(ph.get_plugins('en').count(), 3)

        admin_user, staff = self._get_guys()
        endpoint = self.get_clear_placeholder_url(ph, language='en')

        with self.login_user_context(admin_user):
            response = self.client.post(endpoint, {'test': 0})

        self.assertEqual(response.status_code, 302)

        # After cleaning the de placeholder, en placeholder must still have all the plugins
        self.assertEqual(ph.get_plugins('en').count(), 0)

    def test_empty_placeholder_in_correct_language(self):
        """
        Test that Cleaning a placeholder only affect current language contents
        """
        # create some objects
        page_en = create_page("EmptyPlaceholderTestPage (EN)", "nav_playground.html", "en")
        ph = page_en.get_placeholders("en").get(slot="body")

        # add the text plugin to the en version of the page
        add_plugin(ph, "TextPlugin", "en", body="Hello World EN 1")
        add_plugin(ph, "TextPlugin", "en", body="Hello World EN 2")

        # creating a de title of the page and adding plugins to it
        create_title("de", page_en.get_title(), page_en, slug=page_en.get_slug('en'))
        add_plugin(ph, "TextPlugin", "de", body="Hello World DE")
        add_plugin(ph, "TextPlugin", "de", body="Hello World DE 2")
        add_plugin(ph, "TextPlugin", "de", body="Hello World DE 3")

        # before cleaning the de placeholder
        self.assertEqual(ph.get_plugins('en').count(), 2)
        self.assertEqual(ph.get_plugins('de').count(), 3)

        admin_user, staff = self._get_guys()
        endpoint = self.get_clear_placeholder_url(ph, language='de')

        with self.login_user_context(admin_user):
            response = self.client.post(endpoint, {'test': 0})

        self.assertEqual(response.status_code, 302)

        # After cleaning the de placeholder, en placeholder must still have all the plugins
        self.assertEqual(ph.get_plugins('en').count(), 2)
        self.assertEqual(ph.get_plugins('de').count(), 0)


class AdminTests(AdminTestsBase):
    # TODO: needs tests for actual permissions, not only superuser/normaluser

    def setUp(self):
        self.page = create_page("testpage", "nav_playground.html", "en")

    def get_admin(self):
        User = get_user_model()

        fields = dict(email="admin@django-cms.org", is_staff=True, is_superuser=True)

        if (User.USERNAME_FIELD != 'email'):
            fields[User.USERNAME_FIELD] = "admin"

        usr = User(**fields)
        usr.set_password(getattr(usr, User.USERNAME_FIELD))
        usr.save()
        return usr

    def get_permless(self):
        User = get_user_model()

        fields = dict(email="permless@django-cms.org", is_staff=True)

        if (User.USERNAME_FIELD != 'email'):
            fields[User.USERNAME_FIELD] = "permless"

        usr = User(**fields)
        usr.set_password(getattr(usr, User.USERNAME_FIELD))
        usr.save()
        return usr

    def get_page(self):
        return self.page

    def test_change_innavigation(self):
        page = self.get_page()
        permless = self.get_permless()
        admin_user = self.get_admin()
        with self.login_user_context(permless):
            request = self.get_request()
            response = self.admin_class.change_innavigation(request, page.pk)
            self.assertEqual(response.status_code, 405)
        with self.login_user_context(permless):
            request = self.get_request(post_data={'no': 'data'})
            response = self.admin_class.change_innavigation(request, page.pk)
            self.assertEqual(response.status_code, 403)
        with self.login_user_context(permless):
            request = self.get_request(post_data={'no': 'data'})
            self.assertEqual(response.status_code, 403)
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={'no': 'data'})
            self.assertRaises(Http404, self.admin_class.change_innavigation,
                              request, page.pk + 100)
        with self.login_user_context(permless):
            request = self.get_request(post_data={'no': 'data'})
            response = self.admin_class.change_innavigation(request, page.pk)
            self.assertEqual(response.status_code, 403)
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={'no': 'data'})
            old = page.get_in_navigation()
            response = self.admin_class.change_innavigation(request, page.pk)
            self.assertEqual(response.status_code, 204)
            page = self.reload(page)
            self.assertEqual(old, not page.get_in_navigation())

    def test_remove_plugin_requires_post(self):
        ph = self.page.get_placeholders('en')[0]
        plugin = add_plugin(ph, 'TextPlugin', 'en', body='test')
        admin_user = self.get_admin()
        with self.login_user_context(admin_user):
            endpoint = self.get_delete_plugin_uri(plugin)
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)

    def test_preview_page(self):
        permless = self.get_permless()
        with self.login_user_context(permless):
            request = self.get_request()
            self.assertRaises(Http404, self.admin_class.preview_page, request, 404, "en")
        page = self.get_page()
        page.set_as_homepage()

        new_site = Site.objects.create(id=2, domain='django-cms.org', name='django-cms')
        new_page = create_page("testpage", "nav_playground.html", "fr", site=new_site)

        base_url = page.get_absolute_url()
        with self.login_user_context(permless):
            request = self.get_request('/?public=true')
            response = self.admin_class.preview_page(request, page.pk, 'en')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], '%s?%s' % (base_url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))
            request = self.get_request()
            response = self.admin_class.preview_page(request, page.pk, 'en')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], '%s?%s' % (base_url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))

            # Switch active site
            request.session['cms_admin_site'] = new_site.pk

            # Preview page attached to active site but not to current site
            response = self.admin_class.preview_page(request, new_page.pk, 'fr')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'],
                             'http://django-cms.org/fr/testpage/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))

    def test_too_many_plugins_global(self):
        conf = {
            'body': {
                'limits': {
                    'global': 1,
                },
            },
        }
        admin_user = self.get_admin()
        url = admin_reverse('cms_placeholder_add_plugin')
        with self.settings(CMS_PERMISSION=False, CMS_PLACEHOLDER_CONF=conf):
            page = create_page('somepage', 'nav_playground.html', 'en')
            body = page.get_placeholders("en").get(slot='body')
            add_plugin(body, 'TextPlugin', 'en', body='text')
            with self.login_user_context(admin_user):
                data = {
                    'plugin_type': 'TextPlugin',
                    'placeholder_id': body.pk,
                    'target_language': 'en',
                }
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)

    def test_too_many_plugins_type(self):
        conf = {
            'body': {
                'limits': {
                    'TextPlugin': 1,
                },
            },
        }
        admin_user = self.get_admin()
        url = admin_reverse('cms_placeholder_add_plugin')
        with self.settings(CMS_PERMISSION=False, CMS_PLACEHOLDER_CONF=conf):
            page = create_page('somepage', 'nav_playground.html', 'en')
            body = page.get_placeholders("en").get(slot='body')
            add_plugin(body, 'TextPlugin', 'en', body='text')
            with self.login_user_context(admin_user):
                data = {
                    'plugin_type': 'TextPlugin',
                    'placeholder_id': body.pk,
                    'target_language': 'en',
                    'plugin_parent': '',
                }
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)

    def test_edit_title_fields_title(self):
        language = "en"
        admin_user = self.get_admin()
        page = create_page('A', 'nav_playground.html', language)
        admin_url = reverse("admin:cms_page_edit_title_fields", args=(
            page.pk, language
        ))
        with self.login_user_context(admin_user):
            self.client.post(admin_url, {'title': "A Title"})
            self.assertEquals(page.get_page_title('en', force_reload=True), 'A Title')


class NoDBAdminTests(CMSTestCase):
    @property
    def admin_class(self):
        return site._registry[Page]

    def test_lookup_allowed_site__exact(self):
        self.assertTrue(self.admin_class.lookup_allowed('site__exact', '1'))

    def test_lookup_allowed_published(self):
        self.assertTrue(self.admin_class.lookup_allowed('published', value='1'))


class PluginPermissionTests(AdminTestsBase):
    def setUp(self):
        self._page = create_page('test page', 'nav_playground.html', 'en')
        self._placeholder = self._page.get_placeholders('en')[0]

    def _get_admin(self):
        User = get_user_model()

        fields = dict(email="admin@django-cms.org", is_staff=True, is_active=True)

        if (User.USERNAME_FIELD != 'email'):
            fields[User.USERNAME_FIELD] = "admin"

        admin_user = User(**fields)

        admin_user.set_password('admin')
        admin_user.save()
        return admin_user

    def _get_page_admin(self):
        return admin.site._registry[Page]

    def _give_permission(self, user, model, permission_type, save=True):
        codename = '%s_%s' % (permission_type, model._meta.object_name.lower())
        user.user_permissions.add(Permission.objects.get(codename=codename))

    def _give_page_permission_rights(self, user):
        self._give_permission(user, PagePermission, 'add')
        self._give_permission(user, PagePermission, 'change')
        self._give_permission(user, PagePermission, 'delete')

    def _get_change_page_request(self, user, page):
        return type('Request', (object,), {
            'user': user,
            'path': base.URL_CMS_PAGE_CHANGE % page.pk
        })

    def _give_cms_permissions(self, user, save=True):
        for perm_type in ['add', 'change', 'delete']:
            for model in [Page, PageContent]:
                self._give_permission(user, model, perm_type, False)
        gpp = GlobalPagePermission.objects.create(
            user=user,
            can_change=True,
            can_delete=True,
            can_change_advanced_settings=False,
            can_publish=True,
            can_change_permissions=False,
            can_move_page=True,
        )
        gpp.sites = Site.objects.all()
        if save:
            user.save()

    def _create_plugin(self):
        plugin = add_plugin(self._placeholder, 'TextPlugin', 'en')
        return plugin

    def test_plugin_edit_wrong_url(self):
        """User tries to edit a plugin using a random url. 404 response returned"""
        plugin = self._create_plugin()
        _, normal_guy = self._get_guys()

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='test@test.com', password='test@test.com')
        else:
            self.client.login(username='test', password='test')

        self._give_permission(normal_guy, Text, 'change')
        endpoint = '%sedit-plugin/%s/' % (admin_reverse('cms_placeholder_edit_plugin', args=[plugin.id]), plugin.id)
        endpoint += '?cms_path=/en/'
        response = self.client.post(endpoint, dict())

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTrue("Page not found" in force_text(response.content))


class AdminFormsTests(AdminTestsBase):
    def test_clean_overwrite_url(self):
        """
        A manual path needs to be stripped from leading and trailing slashes.
        """
        superuser = self.get_superuser()
        cms_page = create_page('test page', 'nav_playground.html', 'en')
        page_data = {
            'overwrite_url': '/overwrite/url/',
            'template': cms_page.get_template(),
        }
        endpoint = self.get_admin_url(Page, 'advanced', cms_page.pk)

        with self.login_user_context(superuser):
            response = self.client.post(endpoint, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            self.assertSequenceEqual(
                cms_page.urls.values_list('path', 'managed'),
                [('overwrite/url', False)],
            )

    def test_missmatching_site_parent_dotsite(self):
        superuser = self.get_superuser()
        new_site = Site.objects.create(id=2, domain='foo.com', name='foo.com')
        parent_page = api.create_page("test", get_cms_setting('TEMPLATES')[0][0], "fr", site=new_site)
        new_page_data = {
            'title': 'Title',
            'slug': 'slug',
            'parent_node': parent_page.node.pk,
        }
        with self.login_user_context(superuser):
            # Invalid parent
            response = self.client.post(self.get_admin_url(Page, 'add'), new_page_data)
            expected_error = (
                '<ul class="errorlist">'
                '<li>Site doesn&#39;t match the parent&#39;s page site</li></ul>'
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_error, html=True)

    def test_form_errors(self):
        superuser = self.get_superuser()
        site0 = Site.objects.create(id=2, domain='foo.com', name='foo.com')
        page1 = api.create_page("test", get_cms_setting('TEMPLATES')[0][0], "fr", site=site0)

        new_page_data = {
            'title': 'Title',
            'slug': 'home',
            'parent_node': page1.node.pk,
        }

        with self.login_user_context(superuser):
            # Invalid parent
            response = self.client.post(self.get_admin_url(Page, 'add'), new_page_data)
            expected_error = (
                '<ul class="errorlist">'
                '<li>Site doesn&#39;t match the parent&#39;s page site</li></ul>'
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_error, html=True)

        new_page_data = {
            'title': 'Title',
            'slug': '#',
        }

        with self.login_user_context(superuser):
            # Invalid slug
            response = self.client.post(self.get_admin_url(Page, 'add'), new_page_data)
            expected_error = '<ul class="errorlist"><li>Slug must not be empty.</li></ul>'
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_error, html=True)

        page2 = api.create_page("test", get_cms_setting('TEMPLATES')[0][0], "en")
        new_page_data = {
            'title': 'Title',
            'slug': 'test',
        }

        with self.login_user_context(superuser):
            # Duplicate slug / path
            response = self.client.post(self.get_admin_url(Page, 'add'), new_page_data)
            expected_error = (
                '<ul class="errorlist"><li>Page '
                '<a href="{}" target="_blank">test</a> '
                'has the same url \'test\' as current page.</li></ul>'
            ).format(self.get_admin_url(Page, 'change', page2.pk))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_error, html=True)

    def test_reverse_id_error_location(self):
        superuser = self.get_superuser()
        create_page('Page 1', 'nav_playground.html', 'en', reverse_id='p1')
        page2 = create_page('Page 2', 'nav_playground.html', 'en')
        page2_endpoint = self.get_admin_url(Page, 'advanced', page2.pk)

        # Assemble a bunch of data to test the page form
        page2_data = {
            'reverse_id': 'p1',
            'template': 'col_two.html',
        }

        with self.login_user_context(superuser):
            response = self.client.post(page2_endpoint, page2_data)
            expected_error = (
                '<ul class="errorlist">'
                '<li>A page with this reverse URL id exists already.</li></ul>'
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_error.format(page2.pk), html=True)

    def test_advanced_settings_endpoint(self):
        admin_user = self.get_superuser()
        site = Site.objects.get_current()
        page = create_page('Page 1', 'nav_playground.html', 'en')
        page_data = {
            'site': site.pk,
            'template': 'col_two.html',
        }
        path = admin_reverse('cms_page_advanced', args=(page.pk,))

        with self.login_user_context(admin_user):
            en_path = path + u"?language=en"
            redirect_path = admin_reverse('cms_page_changelist') + '?language=en'
            response = self.client.post(en_path, page_data)
            self.assertRedirects(response, redirect_path)
            self.assertEqual(Page.objects.get(pk=page.pk).get_template(), 'col_two.html')

        # Now switch it up by adding german as the current language
        # Note that german has not been created as page translation.
        page_data['template'] = 'nav_playground.html'

        with self.login_user_context(admin_user):
            de_path = path + u"?language=de"
            redirect_path = admin_reverse('cms_page_change', args=(page.pk,)) + '?language=de'
            response = self.client.post(de_path, page_data)
            # Assert user is redirected to basic settings.
            self.assertRedirects(response, redirect_path)
            # Make sure no change was made
            self.assertEqual(Page.objects.get(pk=page.pk).get_template('de'), 'col_two.html')

        create_title('de', title='Page 1', page=page.reload())

        # Now try again but slug is set to empty string.
        page.update_urls('de', slug='')
        page_data['language'] = 'de'
        page_data['template'] = 'nav_playground.html'

        with self.login_user_context(admin_user):
            de_path = path + u"?language=de"
            response = self.client.post(de_path, page_data)
            # Assert user is not redirected because there was a form error
            self.assertEqual(response.status_code, 200)
            # Make sure no change was made
            self.assertEqual(Page.objects.get(pk=page.pk).get_template(), 'col_two.html')

        # Now try again but with the title having a slug.
        page.update_urls('de', slug='someslug')
        page_data['language'] = 'de'
        page_data['template'] = 'nav_playground.html'

        with self.login_user_context(admin_user):
            en_path = path + u"?language=de"
            redirect_path = admin_reverse('cms_page_changelist') + '?language=de'
            response = self.client.post(en_path, page_data)
            self.assertRedirects(response, redirect_path)
            self.assertEqual(Page.objects.get(pk=page.pk).get_template('de'), 'nav_playground.html')

    def test_advanced_settings_endpoint_fails_gracefully(self):
        admin_user = self.get_superuser()
        page = create_page('Page 1', 'nav_playground.html', 'en')
        page_data = {
            'language': 'en',
            'template': 'col_two.html',
        }
        path = admin_reverse('cms_page_advanced', args=(page.pk,))

        # It's important to test fields that are validated
        # automatically by Django vs fields that are validated
        # via the clean() method by us.
        # Fields validated by Django will not be in cleaned data
        # if they have an error so if we rely on these in the clean()
        # method then an error will be raised.

        # So test that the form short circuits if there's errors.
        page_data['application_urls'] = 'TestApp'

        with self.login_user_context(admin_user):
            response = self.client.post(path, page_data)
            # Assert user is not redirected because there was a form error
            self.assertEqual(response.status_code, 200)

            page = page.reload()
            # Make sure no change was made
            self.assertEqual(page.application_urls, None)

    def test_create_page_type(self):
        page = create_page('Test', 'static.html', 'en', reverse_id="home")
        for placeholder in page.get_placeholders('en'):
            add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')
        self.assertEqual(Page.objects.count(), 1)
        self.assertEqual(CMSPlugin.objects.count(), 2)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            # source is hidden because there's no page-types
            response = self.client.get(self.get_admin_url(Page, 'add'))
            self.assertContains(response, '<input id="id_source" name="source" type="hidden" />', html=True)
            # create our first page type
            page_data = {'source': page.pk, 'title': 'type1', 'slug': 'type1', '_save': 1}
            response = self.client.post(
                self.get_admin_url(PageType, 'add'),
                data=page_data,
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(Page.objects.count(), 3)
            self.assertEqual(Page.objects.filter(is_page_type=True).count(), 2)
            self.assertEqual(CMSPlugin.objects.count(), 4)
            new_page_id = Page.objects.filter(is_page_type=True).only('pk').latest('id').pk
            response = self.client.get(admin_reverse('cms_page_add'))
            expected_field = (
                '<select id="id_source" name="source">'
                '<option value="" selected="selected">---------</option>'
                '<option value="{}">type1</option></select>'
            ).format(new_page_id)
            self.assertContains(response, expected_field, html=True)
            # source is hidden when adding a page-type
            response = self.client.get(self.get_admin_url(PageType, 'add'))
            self.assertContains(response, '<input id="id_source" name="source" type="hidden" />', html=True)

    def test_render_edit_mode(self):
        from django.core.cache import cache

        cache.clear()

        homepage = create_page('Test', 'static.html', 'en')
        homepage.set_as_homepage()

        for placeholder in homepage.get_placeholders('en'):
            add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')

        user = self.get_superuser()
        self.assertEqual(homepage.get_placeholders('en').count(), 2)
        with self.login_user_context(user):
            output = force_text(
                self.client.get(
                    '/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
                ).content
            )
            self.assertIn('<b>Test</b>', output)
            self.assertEqual(StaticPlaceholder.objects.count(), 2)
            for placeholder in homepage.get_placeholders('en'):
                add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')
            output = force_text(
                self.client.get(
                    '/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
                ).content
            )
            self.assertIn('<b>Test</b>', output)

    def test_tree_view_queries(self):
        from django.core.cache import cache

        cache.clear()
        for i in range(10):
            create_page('Test%s' % i, 'col_two.html', 'en')
        for placeholder in Placeholder.objects.all():
            add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')

        user = self.get_superuser()
        with self.login_user_context(user):
            with self.assertNumQueries(9):
                force_text(self.client.get(self.get_admin_url(Page, 'changelist')))

    def test_smart_link_pages(self):
        admin, staff_guy = self._get_guys()
        page_url = URL_CMS_PAGE_PUBLISHED  # Not sure how to achieve this with reverse...
        create_page('home', 'col_two.html', 'en')

        with self.login_user_context(staff_guy):
            multi_title_page = create_page('main_title', 'col_two.html', 'en',
                                           overwrite_url='overwritten_url',
                                           menu_title='menu_title')

            title = multi_title_page.get_title_obj()
            title.page_title = 'page_title'
            title.save()

            multi_title_page.save()

            # Non ajax call should return a 403 as this page shouldn't be accessed by anything else but ajax queries
            self.assertEqual(403, self.client.get(page_url).status_code)

            self.assertEqual(200,
                             self.client.get(page_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code
            )

            # Test that the query param is working as expected.
            self.assertEqual(1, len(json.loads(self.client.get(page_url, {'q':'main_title'},
                                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest').content.decode("utf-8"))))

            self.assertEqual(1, len(json.loads(self.client.get(page_url, {'q':'menu_title'},
                                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest').content.decode("utf-8"))))

            self.assertEqual(1, len(json.loads(self.client.get(page_url, {'q':'overwritten_url'},
                                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest').content.decode("utf-8"))))

            self.assertEqual(1, len(json.loads(self.client.get(page_url, {'q':'page_title'},
                                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest').content.decode("utf-8"))))


class AdminPageEditContentSizeTests(AdminTestsBase):
    """
    System user count influences the size of the page edit page,
    but the users are only 2 times present on the page

    The test relates to extra=0
    at PagePermissionInlineAdminForm and ViewRestrictionInlineAdmin
    """

    def test_editpage_contentsize(self):
        """
        Expected a username only 2 times in the content, but a relationship
        between usercount and pagesize
        """
        with self.settings(CMS_PERMISSION=True):
            admin_user = self.get_superuser()
            PAGE_NAME = 'TestPage'
            USER_NAME = 'test_size_user_0'
            current_site = Site.objects.get(pk=1)
            page = create_page(PAGE_NAME, "nav_playground.html", "en", site=current_site, created_by=admin_user)
            page.save()
            self._page = page
            with self.login_user_context(admin_user):
                url = base.URL_CMS_PAGE_PERMISSION_CHANGE % self._page.pk
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                old_response_size = len(response.content)
                old_user_count = get_user_model().objects.count()
                # create additionals user and reload the page
                get_user_model().objects.create_user(username=USER_NAME, email=USER_NAME + '@django-cms.org',
                                                     password=USER_NAME)
                user_count = get_user_model().objects.count()
                more_users_in_db = old_user_count < user_count
                # we have more users
                self.assertTrue(more_users_in_db, "New users got NOT created")
                response = self.client.get(url)
                new_response_size = len(response.content)
                page_size_grown = old_response_size < new_response_size
                # expect that the pagesize gets influenced by the useramount of the system
                self.assertTrue(page_size_grown, "Page size has not grown after user creation")
                # usernames are only 2 times in content
                text = smart_str(response.content, response.charset)
                foundcount = text.count(USER_NAME)
                # 2 forms contain usernames as options
                self.assertEqual(foundcount, 2,
                                 "Username %s appeared %s times in response.content, expected 2 times" % (
                                     USER_NAME, foundcount))


class AdminPageTreeTests(AdminTestsBase):

    def test_move_node(self):
        admin_user, staff = self._get_guys()
        page_admin = self.admin_class

        alpha = create_page('Alpha', 'nav_playground.html', 'en')
        beta = create_page('Beta', TEMPLATE_INHERITANCE_MAGIC, 'en')
        gamma = create_page('Gamma', TEMPLATE_INHERITANCE_MAGIC, 'en')
        delta = create_page('Delta', TEMPLATE_INHERITANCE_MAGIC, 'en')

        # Current structure:
        #   <root>
        #   ⊢ Alpha
        #   ⊢ Beta
        #   ⊢ Gamma
        #   ⊢ Delta

        # Move Beta to be a child of Alpha
        data = {
            'id': beta.pk,
            'position': 0,
            'target': alpha.pk,
        }

        with self.login_user_context(admin_user):
            request = self.get_request(post_data=data)
            response = page_admin.move_page(request, page_id=beta.pk)
            data = json.loads(response.content.decode('utf8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 200)
        self.assertEqual(alpha.node._reload().get_descendants().count(), 1)

        # Current structure:
        #   <root>
        #   ⊢ Alpha
        #       ⊢ Beta
        #   ⊢ Gamma
        #   ⊢ Delta

        # Move Gamma to be a child of Beta
        data = {
            'id': gamma.pk,
            'position': 0,
            'target': beta.pk,
        }

        with self.login_user_context(admin_user):
            request = self.get_request(post_data=data)
            response = page_admin.move_page(request, page_id=gamma.pk)
            data = json.loads(response.content.decode('utf8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 200)
        self.assertEqual(alpha.node._reload().get_descendants().count(), 2)
        self.assertEqual(beta.node._reload().get_descendants().count(), 1)

        # Current structure:
        #   <root>
        #   ⊢ Alpha
        #       ⊢ Beta
        #           ⊢ Gamma
        #   ⊢ Delta

        # Move Delta to be a child of Beta
        data = {
            'id': delta.pk,
            'position': 0,
            'target': gamma.pk,
        }

        with self.login_user_context(admin_user):
            request = self.get_request(post_data=data)
            response = page_admin.move_page(request, page_id=delta.pk)
            data = json.loads(response.content.decode('utf8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 200)
        self.assertEqual(alpha.node._reload().get_descendants().count(), 3)
        self.assertEqual(beta.node._reload().get_descendants().count(), 2)
        self.assertEqual(gamma.node._reload().get_descendants().count(), 1)

        # Current structure:
        #   <root>
        #   ⊢ Alpha
        #       ⊢ Beta
        #           ⊢ Gamma
        #               ⊢ Delta

        # Move Beta to the root as node #1 (positions are 0-indexed)
        data = {
            'id': beta.pk,
            'position': 1,
        }

        with self.login_user_context(admin_user):
            request = self.get_request(post_data=data)
            response = page_admin.move_page(request, page_id=beta.pk)
            data = json.loads(response.content.decode('utf8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 200)
        self.assertEqual(alpha.node._reload().get_descendants().count(), 0)
        self.assertEqual(beta.node._reload().get_descendants().count(), 2)
        self.assertEqual(gamma.node._reload().get_descendants().count(), 1)

        # Current structure:
        #   <root>
        #   ⊢ Alpha
        #   ⊢ Beta
        #       ⊢ Gamma
        #           ⊢ Delta

        # Move Beta to be a child of Alpha again
        data = {
            'id': beta.pk,
            'position': 0,
            'target': alpha.pk,
        }

        with self.login_user_context(admin_user):
            request = self.get_request(post_data=data)
            response = page_admin.move_page(request, page_id=beta.pk)
            data = json.loads(response.content.decode('utf8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 200)
        self.assertEqual(alpha.node._reload().get_descendants().count(), 3)
        self.assertEqual(beta.node._reload().get_descendants().count(), 2)
        self.assertEqual(gamma.node._reload().get_descendants().count(), 1)

        # Current structure:
        #   <root>
        #   ⊢ Alpha
        #       ⊢ Beta
        #           ⊢ Gamma
        #               ⊢ Delta

        # Move Gamma to the root as node #1 (positions are 0-indexed)
        data = {
            'id': gamma.pk,
            'position': 1,
        }

        with self.login_user_context(admin_user):
            request = self.get_request(post_data=data)
            response = page_admin.move_page(request, page_id=gamma.pk)
            data = json.loads(response.content.decode('utf8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 200)
        self.assertEqual(alpha.node._reload().get_descendants().count(), 1)
        self.assertEqual(beta.node._reload().get_descendants().count(), 0)
        self.assertEqual(gamma.node._reload().get_descendants().count(), 1)

        # Current structure:
        #   <root>
        #   ⊢ Alpha
        #       ⊢ Beta
        #   ⊢ Gamma
        #       ⊢ Delta

        # Move Delta to the root as node #1 (positions are 0-indexed)
        data = {
            'id': delta.pk,
            'position': 1,
        }

        with self.login_user_context(admin_user):
            request = self.get_request(post_data=data)
            response = page_admin.move_page(request, page_id=delta.pk)
            data = json.loads(response.content.decode('utf8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 200)
        self.assertEqual(alpha.node._reload().get_descendants().count(), 1)
        self.assertEqual(beta.node._reload().get_descendants().count(), 0)
        self.assertEqual(gamma.node._reload().get_descendants().count(), 0)

        # Current structure:
        #   <root>
        #   ⊢ Alpha
        #       ⊢ Beta
        #   ⊢ Delta
        #   ⊢ Gamma

        # Move Gamma to be a child of Delta
        data = {
            'id': gamma.pk,
            'position': 1,
            'target': delta.pk,
        }

        with self.login_user_context(admin_user):
            request = self.get_request(post_data=data)
            response = page_admin.move_page(request, page_id=gamma.pk)
            data = json.loads(response.content.decode('utf8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 200)
        self.assertEqual(alpha.node._reload().get_descendants().count(), 1)
        self.assertEqual(beta.node._reload().get_descendants().count(), 0)
        self.assertEqual(gamma.node._reload().get_descendants().count(), 0)
        self.assertEqual(delta.node._reload().get_descendants().count(), 1)

        # Final structure:
        #   <root>
        #   ⊢ Alpha
        #       ⊢ Beta
        #   ⊢ Delta
        #       ⊢ Gamma
