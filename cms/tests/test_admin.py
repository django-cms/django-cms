# -*- coding: utf-8 -*-
from __future__ import with_statement
import json
import datetime

from djangocms_text_ckeditor.cms_plugins import TextPlugin
from djangocms_text_ckeditor.models import Text
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.sites import site, AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, AnonymousUser
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import (Http404, HttpResponseBadRequest, HttpResponseForbidden, HttpResponse,
                         QueryDict, HttpResponseNotFound)
from django.utils.encoding import force_text, smart_str
from django.utils import timezone
from django.utils.six.moves.urllib.parse import urlparse

from cms.admin.change_list import CMSChangeList
from cms.admin.forms import PageForm, AdvancedSettingsForm
from cms.admin.pageadmin import PageAdmin
from cms.admin.permissionadmin import PagePermissionInlineAdmin
from cms import api
from cms.api import create_page, create_title, add_plugin, assign_user_to_page, publish_page
from cms.constants import PLUGIN_MOVE_ACTION
from cms.models import UserSettings, StaticPlaceholder
from cms.models.pagemodel import Page
from cms.models.permissionmodels import GlobalPagePermission, PagePermission
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import Title
from cms.test_utils import testcases as base
from cms.test_utils.testcases import (
    CMSTestCase, URL_CMS_PAGE_DELETE, URL_CMS_PAGE,URL_CMS_TRANSLATION_DELETE,
    URL_CMS_PAGE_CHANGE_LANGUAGE, URL_CMS_PAGE_CHANGE, URL_CMS_PAGE_PERMISSIONS,
    URL_CMS_PAGE_ADD, URL_CMS_PAGE_PUBLISHED
)
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.utils import get_cms_setting
from cms.utils.i18n import force_language
from cms.utils.compat import DJANGO_1_6, DJANGO_1_7
from cms.utils.urlutils import admin_reverse


class AdminTestsBase(CMSTestCase):
    @property
    def admin_class(self):
        return site._registry[Page]

    def _get_guys(self, admin_only=False, use_global_permissions=True):
        admin_user = self.get_superuser()
        if admin_only:
            return admin_user
        USERNAME = 'test'

        if get_user_model().USERNAME_FIELD == 'email':
            normal_guy = get_user_model().objects.create_user(USERNAME, 'test@test.com', 'test@test.com')
        else:
            normal_guy = get_user_model().objects.create_user(USERNAME, 'test@test.com', USERNAME)

        normal_guy.is_staff = True
        normal_guy.is_active = True
        normal_guy.save()
        normal_guy.user_permissions = Permission.objects.filter(
            codename__in=['change_page', 'change_title', 'add_page', 'add_title', 'delete_page', 'delete_title']
        )
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
            gpp.sites = Site.objects.all()
        return admin_user, normal_guy


class AdminTestCase(AdminTestsBase):

    def test_extension_not_in_admin(self):
        admin_user, staff = self._get_guys()
        with self.login_user_context(admin_user):
            request = self.get_request(URL_CMS_PAGE_CHANGE % 1, 'en',)
            response = site.index(request)
            self.assertNotContains(response, '/mytitleextension/')
            self.assertNotContains(response, '/mypageextension/')

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
            resp = self.client.post(base.URL_CMS_PAGE_CHANGE % page.pk, page_data,
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
            resp = self.client.post(base.URL_CMS_PAGE_CHANGE % page.pk, page_data,
                                    follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateNotUsed(resp, 'admin/login.html')
            page = Page.objects.get(pk=page.pk)

            self.assertEqual(page.get_title(), OLD_PAGE_NAME)
            self.assertEqual(page.reverse_id, REVERSE_ID)
            title = page.get_title_obj()
            self.assertEqual(title.overwrite_url, OVERRIDE_URL)

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
            resp = self.client.post(base.URL_CMS_PAGE_CHANGE % page.pk, page_data,
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
            resp = self.client.post(base.URL_CMS_PAGE_ADVANCED_CHANGE % page.pk, page_data,
                                    follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateNotUsed(resp, 'admin/login.html')
            resp = self.client.post(base.URL_CMS_PAGE_CHANGE % page.pk, page_data,
                                    follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateNotUsed(resp, 'admin/login.html')
            page = Page.objects.get(pk=page.pk)

            self.assertEqual(page.get_title(), OLD_PAGE_NAME)
            self.assertEqual(page.reverse_id, REVERSE_ID)
            self.assertEqual(page.application_urls, '')

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
            'slug': page2.get_slug(),
            'language': 'en',
            'site': page.site.pk,
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
                           created_by=admin_user, published=True)
        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        create_page('child-page', "nav_playground.html", "en",
                    created_by=admin_user, published=True, parent=page)
        body = page.placeholders.get(slot='body')
        add_plugin(body, 'TextPlugin', 'en', body='text')
        page.publish('en')
        with self.login_user_context(admin_user):
            data = {'post': 'yes'}
            response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)
            self.assertRedirects(response, URL_CMS_PAGE)

    def test_delete_diff_language(self):
        admin_user = self.get_superuser()
        create_page("home", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        page = create_page("delete-page", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
        create_page('child-page', "nav_playground.html", "de",
                    created_by=admin_user, published=True, parent=page)
        body = page.placeholders.get(slot='body')
        add_plugin(body, 'TextPlugin', 'en', body='text')
        page.publish('en')
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
                    created_by=superuser, published=True)
        with self.login_user_context(superuser):
            url = admin_reverse('cms_page_changelist')
            response = self.client.get('%s?template__exact=nav_playground.html' % url)
            errmsg = response.content
            self.assertEqual(response.status_code, 200, errmsg)

    def test_delete_translation(self):
        admin_user = self.get_superuser()
        page = create_page("delete-page-translation", "nav_playground.html", "en",
                           created_by=admin_user, published=True)
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

    def test_change_dates(self):
        admin_user, staff = self._get_guys()

        with self.settings(USE_TZ=False, TIME_ZONE='UTC'):

            page = create_page('test-page', 'nav_playground.html', 'en')
            page.publish('en')
            draft = page.get_draft_object()

            original_date = draft.publication_date
            original_end_date = draft.publication_end_date
            new_date = timezone.now() - datetime.timedelta(days=1)
            new_end_date = timezone.now() + datetime.timedelta(days=1)
            url = admin_reverse('cms_page_dates', args=(draft.pk,))
            with self.login_user_context(admin_user):
                response = self.client.post(url, {
                    'language': 'en',
                    'site': draft.site.pk,
                    'publication_date_0': new_date.date(),
                    'publication_date_1': new_date.strftime("%H:%M:%S"),
                    'publication_end_date_0': new_end_date.date(),
                    'publication_end_date_1': new_end_date.strftime("%H:%M:%S"),
                })
                self.assertEqual(response.status_code, 302)
                draft = Page.objects.get(pk=draft.pk)
                self.assertNotEqual(draft.publication_date.timetuple(), original_date.timetuple())
                self.assertEqual(draft.publication_date.timetuple(), new_date.timetuple())
                self.assertEqual(draft.publication_end_date.timetuple(), new_end_date.timetuple())
                if original_end_date:
                    self.assertNotEqual(draft.publication_end_date.timetuple(), original_end_date.timetuple())

        with self.settings(USE_TZ=True, TIME_ZONE='UTC'):

            page = create_page('test-page-2', 'nav_playground.html', 'en')
            page.publish('en')
            draft = page.get_draft_object()

            original_date = draft.publication_date
            original_end_date = draft.publication_end_date
            new_date = timezone.localtime(timezone.now()) - datetime.timedelta(days=1)
            new_end_date = timezone.localtime(timezone.now()) + datetime.timedelta(days=1)
            url = admin_reverse('cms_page_dates', args=(draft.pk,))
            with self.login_user_context(admin_user):
                response = self.client.post(url, {
                    'language': 'en',
                    'site': draft.site.pk,
                    'publication_date_0': new_date.date(),
                    'publication_date_1': new_date.strftime("%H:%M:%S"),
                    'publication_end_date_0': new_end_date.date(),
                    'publication_end_date_1': new_end_date.strftime("%H:%M:%S"),
                })
                self.assertEqual(response.status_code, 302)
                draft = Page.objects.get(pk=draft.pk)
                self.assertNotEqual(draft.publication_date.timetuple(), original_date.timetuple())
                self.assertEqual(timezone.localtime(draft.publication_date).timetuple(), new_date.timetuple())
                self.assertEqual(timezone.localtime(draft.publication_end_date).timetuple(), new_end_date.timetuple())
                if original_end_date:
                    self.assertNotEqual(draft.publication_end_date.timetuple(), original_end_date.timetuple())

    def test_change_template(self):
        admin_user, staff = self._get_guys()
        request = self.get_request(URL_CMS_PAGE_CHANGE % 1, 'en')
        request.method = "POST"
        pageadmin = site._registry[Page]
        with self.login_user_context(staff):
            self.assertRaises(Http404, pageadmin.change_template, request, 1)
            page = create_page('test-page', 'nav_playground.html', 'en')
            response = pageadmin.change_template(request, page.pk)
            self.assertEqual(response.status_code, 403)
        url = admin_reverse('cms_page_change_template', args=(page.pk,))
        with self.login_user_context(admin_user):
            response = self.client.post(url, {'template': 'doesntexist'})
            self.assertEqual(response.status_code, 400)
            response = self.client.post(url, {'template': get_cms_setting('TEMPLATES')[0][0]})
            self.assertEqual(response.status_code, 200)

    def test_get_permissions(self):
        page = create_page('test-page', 'nav_playground.html', 'en')
        url = admin_reverse('cms_page_get_permissions', args=(page.pk,))
        response = self.client.get(url)
        if DJANGO_1_6:
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'admin/login.html')
        else:
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, '/en/admin/login/?next=%s' % (URL_CMS_PAGE_PERMISSIONS % page.pk))
        admin_user = self.get_superuser()
        with self.login_user_context(admin_user):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateNotUsed(response, 'admin/login.html')

    def test_changelist_items(self):
        admin_user = self.get_superuser()
        first_level_page = create_page('level1', 'nav_playground.html', 'en')
        second_level_page_top = create_page('level21', "nav_playground.html", "en",
                                            created_by=admin_user, published=True, parent=first_level_page)
        second_level_page_bottom = create_page('level22', "nav_playground.html", "en",
                                               created_by=admin_user, published=True,
                                               parent=self.reload(first_level_page))
        third_level_page = create_page('level3', "nav_playground.html", "en",
                                       created_by=admin_user, published=True, parent=second_level_page_top)
        self.assertEqual(Page.objects.all().count(), 4)

        url = admin_reverse('cms_%s_changelist' % Page._meta.model_name)
        request = self.get_request(url)

        request.session = {}
        request.user = admin_user

        page_admin = site._registry[Page]

        cl_params = [request, page_admin.model, page_admin.list_display,
            page_admin.list_display_links, page_admin.list_filter,
            page_admin.date_hierarchy, page_admin.search_fields,
            page_admin.list_select_related, page_admin.list_per_page]
        if hasattr(page_admin, 'list_max_show_all'):  # django 1.4
            cl_params.append(page_admin.list_max_show_all)
        cl_params.extend([page_admin.list_editable, page_admin])
        cl = CMSChangeList(*tuple(cl_params))

        cl.set_items(request)

        root_page = cl.get_items()[0]

        self.assertEqual(root_page, first_level_page)
        self.assertEqual(root_page.get_children()[0], second_level_page_top)
        self.assertEqual(root_page.get_children()[1], second_level_page_bottom)
        self.assertEqual(root_page.get_children()[0].get_children()[0], third_level_page)

    def test_changelist_get_results(self):
        admin_user = self.get_superuser()
        first_level_page = create_page('level1', 'nav_playground.html', 'en', published=True)
        second_level_page_top = create_page('level21', "nav_playground.html", "en",
                                            created_by=admin_user, published=True,
                                            parent=first_level_page)
        second_level_page_bottom = create_page('level22', "nav_playground.html", "en", # nopyflakes
                                               created_by=admin_user, published=True,
                                               parent=self.reload(first_level_page))
        third_level_page = create_page('level3', "nav_playground.html", "en", # nopyflakes
                                       created_by=admin_user, published=True,
                                       parent=second_level_page_top)
        fourth_level_page = create_page('level23', "nav_playground.html", "en", # nopyflakes
                                        created_by=admin_user,
                                        parent=self.reload(first_level_page))
        self.assertEqual(Page.objects.all().count(), 9)

        url = admin_reverse('cms_%s_changelist' % Page._meta.model_name)

        request = self.get_request(url)
        request.session = {}
        request.user = admin_user

        page_admin = site._registry[Page]

        # full blown page list. only draft pages are taken into account
        cl_params = [request, page_admin.model, page_admin.list_display,
            page_admin.list_display_links, page_admin.list_filter,
            page_admin.date_hierarchy, page_admin.search_fields,
            page_admin.list_select_related, page_admin.list_per_page]
        if hasattr(page_admin, 'list_max_show_all'):  # django 1.4
            cl_params.append(page_admin.list_max_show_all)
        cl_params.extend([page_admin.list_editable, page_admin])
        cl = CMSChangeList(*tuple(cl_params))
        cl.get_results(request)
        self.assertEqual(cl.full_result_count, 5)
        self.assertEqual(cl.result_count, 5)

        # only one unpublished page is returned
        request = self.get_request(url+'?q=level23')
        request.session = {}
        request.user = admin_user
        cl_params[0] = request
        cl = CMSChangeList(*tuple(cl_params))
        cl.get_results(request)
        self.assertEqual(cl.full_result_count, 5)
        self.assertEqual(cl.result_count, 1)

        # a number of pages matches the query
        request = self.get_request(url+'?q=level2')
        request.session = {}
        request.user = admin_user
        cl_params[0] = request
        cl = CMSChangeList(*tuple(cl_params))
        cl.get_results(request)
        self.assertEqual(cl.full_result_count, 5)
        self.assertEqual(cl.result_count, 3)

    def test_unihandecode_doesnt_break_404_in_admin(self):
        self.get_superuser()

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='admin@django-cms.org', password='admin@django-cms.org')
        else:
            self.client.login(username='admin', password='admin')

        response = self.client.get(URL_CMS_PAGE_CHANGE_LANGUAGE % (1, 'en'))
        self.assertEqual(response.status_code, 404)

    def test_empty_placeholder_in_correct_language(self):
        """
        Test that Cleaning a placeholder only affect current language contents
        """
        # create some objects
        page_en = create_page("EmptyPlaceholderTestPage (EN)", "nav_playground.html", "en")
        ph = page_en.placeholders.get(slot="body")

        # add the text plugin to the en version of the page
        add_plugin(ph, "TextPlugin", "en", body="Hello World EN 1")
        add_plugin(ph, "TextPlugin", "en", body="Hello World EN 2")

        # creating a de title of the page and adding plugins to it
        create_title("de", page_en.get_title(), page_en, slug=page_en.get_slug())
        add_plugin(ph, "TextPlugin", "de", body="Hello World DE")
        add_plugin(ph, "TextPlugin", "de", body="Hello World DE 2")
        add_plugin(ph, "TextPlugin", "de", body="Hello World DE 3")

        # before cleaning the de placeholder
        self.assertEqual(ph.get_plugins('en').count(), 2)
        self.assertEqual(ph.get_plugins('de').count(), 3)

        admin_user, staff = self._get_guys()
        with self.login_user_context(admin_user):
            url = '%s?language=de' % admin_reverse('cms_page_clear_placeholder', args=[ph.pk])
            response = self.client.post(url, {'test': 0})

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

    def test_change_publish_unpublish(self):
        page = self.get_page()
        permless = self.get_permless()
        with self.login_user_context(permless):
            request = self.get_request()
            response = self.admin_class.publish_page(request, page.pk, "en")
            self.assertEqual(response.status_code, 405)
            page = self.reload(page)
            self.assertFalse(page.is_published('en'))

            request = self.get_request(post_data={'no': 'data'})
            response = self.admin_class.publish_page(request, page.pk, "en")
            self.assertEqual(response.status_code, 403)
            page = self.reload(page)
            self.assertFalse(page.is_published('en'))

        admin_user = self.get_admin()
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={'no': 'data'})
            response = self.admin_class.publish_page(request, page.pk, "en")
            self.assertEqual(response.status_code, 302)

            page = self.reload(page)
            self.assertTrue(page.is_published('en'))

            response = self.admin_class.unpublish(request, page.pk, "en")
            self.assertEqual(response.status_code, 302)

            page = self.reload(page)
            self.assertFalse(page.is_published('en'))

    def test_change_status_adds_log_entry(self):
        page = self.get_page()
        admin_user = self.get_admin()
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={'no': 'data'})
            self.assertFalse(LogEntry.objects.count())
            response = self.admin_class.publish_page(request, page.pk, "en")
            self.assertEqual(response.status_code, 302)
            self.assertEqual(1, LogEntry.objects.count())
            self.assertEqual(page.pk, int(LogEntry.objects.all()[0].object_id))

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
            self.assertRaises(Http404, self.admin_class.change_innavigation,
                              request, page.pk + 100)
        with self.login_user_context(permless):
            request = self.get_request(post_data={'no': 'data'})
            response = self.admin_class.change_innavigation(request, page.pk)
            self.assertEqual(response.status_code, 403)
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={'no': 'data'})
            old = page.in_navigation
            response = self.admin_class.change_innavigation(request, page.pk)
            self.assertEqual(response.status_code, 200)
            page = self.reload(page)
            self.assertEqual(old, not page.in_navigation)

    def test_publish_page_requires_perms(self):
        permless = self.get_permless()
        with self.login_user_context(permless):
            request = self.get_request()
            request.method = "POST"
            response = self.admin_class.publish_page(request, Page.objects.all()[0].pk, "en")
            self.assertEqual(response.status_code, 403)

    def test_revert_page(self):
        self.page.publish('en')
        title = self.page.title_set.get(language='en')
        title.title = 'new'
        title.save()
        self.assertEqual(Title.objects.all().count(), 2)
        self.assertEqual(Page.objects.all().count(), 2)
        with self.login_user_context(self.get_superuser()):
            request = self.get_request()
            request.method = "POST"
            response = self.admin_class.revert_page(request, Page.objects.all()[0].pk, "en")
            self.assertEqual(response.status_code, 302)
        self.assertEqual(Title.objects.all().count(), 2)
        self.assertEqual(Page.objects.all().count(), 2)
        new_title = Title.objects.get(pk=title.pk)
        self.assertNotEqual(title.title, new_title.title)
        self.assertTrue(title.publisher_is_draft)
        self.assertTrue(new_title.publisher_is_draft)

    def test_revert_page_requires_perms(self):
        permless = self.get_permless()
        with self.login_user_context(permless):
            request = self.get_request()
            request.method = "POST"
            response = self.admin_class.revert_page(request, Page.objects.all()[0].pk, 'en')
            self.assertEqual(response.status_code, 403)

    def test_revert_page_redirects(self):
        admin_user = self.get_admin()
        self.page.publish("en")  # Ensure public copy exists before reverting
        with self.login_user_context(admin_user):
            response = self.client.post(admin_reverse('cms_page_revert_page', args=(self.page.pk, 'en')))
            self.assertEqual(response.status_code, 302)
            url = response['Location']
            self.assertTrue(url.endswith('?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')))

    def test_remove_plugin_requires_post(self):
        ph = Placeholder.objects.create(slot='test')
        plugin = add_plugin(ph, 'TextPlugin', 'en', body='test')
        admin_user = self.get_admin()
        with self.login_user_context(admin_user):
            request = self.get_request()
            response = self.admin_class.delete_plugin(request, plugin.pk)
            self.assertEqual(response.status_code, 200)

    def test_move_plugin(self):
        ph = Placeholder.objects.create(slot='test')
        plugin = add_plugin(ph, 'TextPlugin', 'en', body='test')
        page = self.get_page()
        source, target = list(page.placeholders.all())[:2]
        pageplugin = add_plugin(source, 'TextPlugin', 'en', body='test')
        plugin_class = pageplugin.get_plugin_class_instance()

        with force_language('en'):
            action_urls = pageplugin.get_action_urls()

        expected = {
            'reload': plugin_class.requires_reload(PLUGIN_MOVE_ACTION),
            'urls': action_urls,
        }
        placeholder = Placeholder.objects.all()[0]
        permless = self.get_permless()
        admin_user = self.get_admin()
        with self.login_user_context(permless):
            request = self.get_request()
            response = self.admin_class.move_plugin(request)
            self.assertEqual(response.status_code, 405)
            request = self.get_request(post_data={'not_usable': '1'})
            self.assertRaises(RuntimeError, self.admin_class.move_plugin, request)
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={'ids': plugin.pk})
            self.assertRaises(RuntimeError, self.admin_class.move_plugin, request)
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={'plugin_id': pageplugin.pk,
                'placeholder_id': 'invalid-placeholder', 'plugin_language': 'en'})
            self.assertRaises(RuntimeError, self.admin_class.move_plugin, request)
        with self.login_user_context(permless):
            request = self.get_request(post_data={'plugin_id': pageplugin.pk,
                'placeholder_id': placeholder.pk, 'plugin_parent': '', 'plugin_language': 'en'})
            self.assertEqual(self.admin_class.move_plugin(request).status_code, HttpResponseForbidden.status_code)
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={'plugin_id': pageplugin.pk,
                'placeholder_id': placeholder.pk, 'plugin_parent': '', 'plugin_language': 'en'})
            response = self.admin_class.move_plugin(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.content.decode('utf8')), expected)
        with self.login_user_context(permless):
            request = self.get_request(post_data={'plugin_id': pageplugin.pk,
                'placeholder_id': placeholder.id, 'plugin_parent': '', 'plugin_language': 'en'})
            self.assertEqual(self.admin_class.move_plugin(request).status_code, HttpResponseForbidden.status_code)
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={'plugin_id': pageplugin.pk,
                'placeholder_id': placeholder.id, 'plugin_parent': '', 'plugin_language': 'en'})
            response = self.admin_class.move_plugin(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.content.decode('utf8')), expected)

    def test_move_language(self):
        page = self.get_page()
        source, target = list(page.placeholders.all())[:2]
        col = add_plugin(source, 'MultiColumnPlugin', 'en')
        sub_col = add_plugin(source, 'ColumnPlugin', 'en', target=col)
        col2 = add_plugin(source, 'MultiColumnPlugin', 'de')

        admin_user = self.get_admin()
        with self.login_user_context(admin_user):
            request = self.get_request(post_data={
                'plugin_id': sub_col.pk,
                'placeholder_id': source.id,
                'plugin_parent': col2.pk,
                'plugin_language': 'de'
            })
            response = self.admin_class.move_plugin(request)
            self.assertEqual(response.status_code, 200)
        sub_col = CMSPlugin.objects.get(pk=sub_col.pk)
        self.assertEqual(sub_col.language, "de")
        self.assertEqual(sub_col.parent_id, col2.pk)

    def test_preview_page(self):
        permless = self.get_permless()
        with self.login_user_context(permless):
            request = self.get_request()
            self.assertRaises(Http404, self.admin_class.preview_page, request, 404, "en")
        page = self.get_page()
        page.publish("en")
        base_url = page.get_absolute_url()
        with self.login_user_context(permless):
            request = self.get_request('/?public=true')
            response = self.admin_class.preview_page(request, page.pk, 'en')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], '%s?%s&language=en' % (base_url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))
            request = self.get_request()
            response = self.admin_class.preview_page(request, page.pk, 'en')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], '%s?%s&language=en' % (base_url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))
            current_site = Site.objects.create(domain='django-cms.org', name='django-cms')
            page.site = current_site
            page.save()
            page.publish("en")
            self.assertTrue(page.is_home)
            response = self.admin_class.preview_page(request, page.pk, 'en')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'],
                             'http://django-cms.org%s?%s&language=en' % (base_url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))

    def test_too_many_plugins_global(self):
        conf = {
            'body': {
                'limits': {
                    'global': 1,
                },
            },
        }
        admin_user = self.get_admin()
        url = admin_reverse('cms_page_add_plugin')
        with self.settings(CMS_PERMISSION=False, CMS_PLACEHOLDER_CONF=conf):
            page = create_page('somepage', 'nav_playground.html', 'en')
            body = page.placeholders.get(slot='body')
            add_plugin(body, 'TextPlugin', 'en', body='text')
            with self.login_user_context(admin_user):
                data = {
                    'plugin_type': 'TextPlugin',
                    'placeholder_id': body.pk,
                    'plugin_language': 'en',
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
        url = admin_reverse('cms_page_add_plugin')
        with self.settings(CMS_PERMISSION=False, CMS_PLACEHOLDER_CONF=conf):
            page = create_page('somepage', 'nav_playground.html', 'en')
            body = page.placeholders.get(slot='body')
            add_plugin(body, 'TextPlugin', 'en', body='text')
            with self.login_user_context(admin_user):
                data = {
                    'plugin_type': 'TextPlugin',
                    'placeholder_id': body.pk,
                    'plugin_language': 'en',
                    'plugin_parent': '',
                }
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)

    def test_edit_title_dirty_bit(self):
        language = "en"
        admin_user = self.get_admin()
        page = create_page('A', 'nav_playground.html', language)
        page_admin = PageAdmin(Page, None)
        page_admin._current_page = page
        page.publish("en")
        draft_page = page.get_draft_object()
        admin_url = reverse("admin:cms_page_edit_title_fields", args=(
            draft_page.pk, language
        ))

        post_data = {
            'title': "A Title"
        }
        with self.login_user_context(admin_user):
            self.client.post(admin_url, post_data)
            draft_page = Page.objects.get(pk=page.pk).get_draft_object()
            self.assertTrue(draft_page.is_dirty('en'))

    def test_edit_title_languages(self):
        language = "en"
        admin_user = self.get_admin()
        page = create_page('A', 'nav_playground.html', language)
        page_admin = PageAdmin(Page, None)
        page_admin._current_page = page
        page.publish("en")
        draft_page = page.get_draft_object()
        admin_url = reverse("admin:cms_page_edit_title_fields", args=(
            draft_page.pk, language
        ))

        post_data = {
            'title': "A Title"
        }
        with self.login_user_context(admin_user):
            self.client.post(admin_url, post_data)
            draft_page = Page.objects.get(pk=page.pk).get_draft_object()
            self.assertTrue(draft_page.is_dirty('en'))

    def test_page_form_leak(self):
        language = "en"
        admin_user = self.get_admin()
        request = self.get_request('/', 'en')
        request.user = admin_user
        page = create_page('A', 'nav_playground.html', language, menu_title='menu title')
        page_admin = PageAdmin(Page, site)
        page_admin._current_page = page

        edit_form = page_admin.get_form(request, page)
        add_form = page_admin.get_form(request, None)

        self.assertEqual(edit_form.base_fields['menu_title'].initial, 'menu title')
        self.assertEqual(add_form.base_fields['menu_title'].initial, None)


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
        self._placeholder = self._page.placeholders.all()[0]

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
            for model in [Page, Title]:
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

    def test_plugin_add_requires_permissions(self):
        """User tries to add a plugin but has no permissions. He can add the plugin after he got the permissions"""
        admin = self._get_admin()
        self._give_cms_permissions(admin)

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='admin@django-cms.org', password='admin')
        else:
            self.client.login(username='admin', password='admin')

        url = admin_reverse('cms_page_add_plugin')
        data = {
            'plugin_type': 'TextPlugin',
            'placeholder_id': self._placeholder.pk,
            'plugin_language': 'en',
            'plugin_parent': '',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self._give_permission(admin, Text, 'add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)

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
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        # After he got the permissions, he can edit the plugin
        self._give_permission(normal_guy, Text, 'change')
        response = self.client.post(url, dict())
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_plugin_edit_wrong_url(self):
        """User tries to edit a plugin using a random url. 404 response returned"""
        plugin = self._create_plugin()
        _, normal_guy = self._get_guys()

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='test@test.com', password='test@test.com')
        else:
            self.client.login(username='test', password='test')

        self._give_permission(normal_guy, Text, 'change')
        url = '%s/edit-plugin/%s/' % (admin_reverse('cms_page_edit_plugin', args=[plugin.id]), plugin.id)
        response = self.client.post(url, dict())
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTrue("Plugin not found" in force_text(response.content))

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
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
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
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
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
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        # After he got the permissions, he can edit the plugin
        self._give_permission(normal_guy, Text, 'add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_plugins_copy_placeholder_ref(self):
        """
        User copies a placeholder into a clipboard. A PlaceholderReferencePlugin
        is created. Afterwards he copies this into a placeholder and the
        PlaceholderReferencePlugin unpacks its content. After that he clears
        the clipboard.
        """
        self.assertEqual(Placeholder.objects.count(), 2)
        self._create_plugin()
        self._create_plugin()
        admin_user = self.get_superuser()
        clipboard = Placeholder()
        clipboard.save()
        self.assertEqual(CMSPlugin.objects.count(), 2)
        settings = UserSettings(language="fr", clipboard=clipboard, user=admin_user)
        settings.save()
        self.assertEqual(Placeholder.objects.count(), 3)

        if get_user_model().USERNAME_FIELD == 'email':
            self.client.login(username='admin@django-cms.org', password='admin@django-cms.org')
        else:
            self.client.login(username='admin', password='admin')

        url = admin_reverse('cms_page_copy_plugins')
        data = dict(source_plugin_id='',
                    source_placeholder_id=self._placeholder.pk,
                    source_language='en',
                    target_language='en',
                    target_placeholder_id=clipboard.pk,
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        clipboard_plugins = clipboard.get_plugins()
        self.assertEqual(CMSPlugin.objects.count(), 5)
        self.assertEqual(clipboard_plugins.count(), 1)
        self.assertEqual(clipboard_plugins[0].plugin_type, "PlaceholderPlugin")
        placeholder_plugin, _ = clipboard_plugins[0].get_plugin_instance()
        ref_placeholder = placeholder_plugin.placeholder_ref
        copied_plugins = ref_placeholder.get_plugins()
        self.assertEqual(copied_plugins.count(), 2)
        data = dict(source_plugin_id=placeholder_plugin.pk,
                    source_placeholder_id=clipboard.pk,
                    source_language='en',
                    target_language='fr',
                    target_placeholder_id=self._placeholder.pk,
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        plugins = self._placeholder.get_plugins()
        self.assertEqual(plugins.count(), 4)
        self.assertEqual(CMSPlugin.objects.count(), 7)
        self.assertEqual(Placeholder.objects.count(), 4)
        url = admin_reverse('cms_page_clear_placeholder', args=[clipboard.pk])
        with self.assertNumQueries(FuzzyInt(70, 90)):
            response = self.client.post(url, {'test': 0})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CMSPlugin.objects.count(), 4)
        self.assertEqual(Placeholder.objects.count(), 3)

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
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        # After he got the permissions, he can edit the plugin
        self._give_permission(normal_guy, Text, 'add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertEqual(2, CMSPlugin.objects.all().count())

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
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

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

    def test_plugin_add_returns_valid_pk_for_plugin(self):
        admin_user = self._get_admin()
        self._give_cms_permissions(admin_user)
        self._give_permission(admin_user, Text, 'add')

        username = getattr(admin_user, get_user_model().USERNAME_FIELD)
        self.client.login(username=username, password='admin')

        url = admin_reverse('cms_page_add_plugin')
        data = {
            'plugin_type': 'TextPlugin',
            'placeholder_id': self._placeholder.pk,
            'plugin_language': 'en',
            'plugin_parent': '',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertEqual(response['content-type'], 'application/json')
        pk = response.content.decode('utf8').split("edit-plugin/")[1].split("/")[0]
        self.assertTrue(CMSPlugin.objects.filter(pk=int(pk)).exists())


class AdminFormsTests(AdminTestsBase):
    def test_clean_overwrite_url(self):
        user = AnonymousUser()
        user.is_superuser = True
        user.pk = 1
        request = type('Request', (object,), {'user': user})
        with self.settings():
            data = {
                'title': 'TestPage',
                'slug': 'test-page',
                'language': 'en',
                'overwrite_url': '/overwrite/url/',
                'site': Site.objects.get_current().pk,
                'template': get_cms_setting('TEMPLATES')[0][0],
                'published': True
            }

            form = PageForm(data)
            self.assertTrue(form.is_valid(), form.errors.as_text())
            instance = form.save()
            instance.permission_user_cache = user
            instance.permission_advanced_settings_cache = True
            Title.objects.set_or_create(request, instance, form, 'en')
            form = PageForm(data, instance=instance)
            self.assertTrue(form.is_valid(), form.errors.as_text())

    def test_missmatching_site_parent_dotsite(self):
        site0 = Site.objects.create(domain='foo.com', name='foo.com')
        site1 = Site.objects.create(domain='foo2.com', name='foo.com')
        parent_page = Page.objects.create(
            template='nav_playground.html',
            site=site0)
        new_page_data = {
            'title': 'Title',
            'slug': 'slug',
            'language': 'en',
            'site': site1.pk,
            'template': get_cms_setting('TEMPLATES')[0][0],
            'reverse_id': '',
            'parent': parent_page.pk,
        }
        form = PageForm(data=new_page_data, files=None)
        self.assertFalse(form.is_valid())
        self.assertIn(u"Site doesn't match the parent's page site",
                      form.errors['__all__'])

    def test_form_errors(self):

        new_page_data = {
            'title': 'Title',
            'slug': 'home',
            'language': 'en',
            'site': 10,
            'template': get_cms_setting('TEMPLATES')[0][0],
            'reverse_id': '',
        }
        form = PageForm(data=new_page_data, files=None)
        self.assertFalse(form.is_valid())
        site0 = Site.objects.create(domain='foo.com', name='foo.com')
        page1 = api.create_page("test", get_cms_setting('TEMPLATES')[0][0], "fr", site=site0)

        new_page_data = {
            'title': 'Title',
            'slug': 'home',
            'language': 'en',
            'site': 1,
            'template': get_cms_setting('TEMPLATES')[0][0],
            'reverse_id': '',
            'parent': page1.pk,
        }
        form = PageForm(data=new_page_data, files=None)
        self.assertFalse(form.is_valid())

        new_page_data = {
            'title': 'Title',
            'slug': '#',
            'language': 'en',
            'site': 1,
            'template': get_cms_setting('TEMPLATES')[0][0],
            'reverse_id': '',
        }
        form = PageForm(data=new_page_data, files=None)
        self.assertFalse(form.is_valid())

        new_page_data = {
            'title': 'Title',
            'slug': 'home',
            'language': 'pp',
            'site': 1,
            'template': get_cms_setting('TEMPLATES')[0][0],
            'reverse_id': '',
            'parent':'',
        }
        form = PageForm(data=new_page_data, files=None)
        self.assertFalse(form.is_valid())


        page2 = api.create_page("test", get_cms_setting('TEMPLATES')[0][0], "en")
        new_page_data = {
            'title': 'Title',
            'slug': 'test',
            'language': 'en',
            'site': 1,
            'template': get_cms_setting('TEMPLATES')[0][0],
            'reverse_id': '',
            'parent':'',
        }
        form = PageForm(data=new_page_data, files=None)
        self.assertFalse(form.is_valid())

        page3 = api.create_page("test", get_cms_setting('TEMPLATES')[0][0], "en", parent=page2)
        page3.title_set.update(path="hello/")
        page3 = page3.reload()
        new_page_data = {
            'title': 'Title',
            'slug': 'test',
            'language': 'en',
            'site': 1,
            'template': get_cms_setting('TEMPLATES')[0][0],
            'reverse_id': '',
            'parent':'',
        }
        form = PageForm(data=new_page_data, files=None, instance=page3)
        self.assertFalse(form.is_valid())



    def test_reverse_id_error_location(self):
        ''' Test moving the reverse_id validation error to a field specific one '''

        # this is the Reverse ID we'll re-use to break things.
        dupe_id = 'p1'
        curren_site = Site.objects.get_current()
        create_page('Page 1', 'nav_playground.html', 'en', reverse_id=dupe_id)
        page2 = create_page('Page 2', 'nav_playground.html', 'en')
        # Assemble a bunch of data to test the page form
        page2_data = {
            'language': 'en',
            'site': curren_site.pk,
            'reverse_id': dupe_id,
            'template': 'col_two.html',
        }
        form = AdvancedSettingsForm(data=page2_data, files=None)
        self.assertFalse(form.is_valid())

        # reverse_id is the only item that is in __all__ as every other field
        # has it's own clean method. Moving it to be a field error means
        # __all__ is now not available.
        self.assertNotIn('__all__', form.errors)
        # In moving it to it's own field, it should be in form.errors, and
        # the values contained therein should match these.
        self.assertIn('reverse_id', form.errors)
        self.assertEqual(1, len(form.errors['reverse_id']))
        self.assertEqual([u'A page with this reverse URL id exists already.'],
                         form.errors['reverse_id'])
        page2_data['reverse_id'] = ""

        form = AdvancedSettingsForm(data=page2_data, files=None)
        self.assertTrue(form.is_valid())
        admin_user = self._get_guys(admin_only=True)
        # reset some of page2_data so we can use cms.api.create_page
        page2 = page2.reload()
        page2.site = curren_site
        page2.save()
        with self.login_user_context(admin_user):
            # re-reset the page2_data for the admin form instance.
            page2_data['reverse_id'] = dupe_id
            page2_data['site'] = curren_site.pk

            # post to the admin change form for page 2, and test that the
            # reverse_id form row has an errors class. Django's admin avoids
            # collapsing these, so that the error is visible.
            resp = self.client.post(base.URL_CMS_PAGE_ADVANCED_CHANGE % page2.pk, page2_data)
            self.assertContains(resp, '<div class="form-row errors reverse_id">')

    def test_create_page_type(self):
        page = create_page('Test', 'static.html', 'en', published=True, reverse_id="home")
        for placeholder in Placeholder.objects.all():
            add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')
        page.publish('en')
        self.assertEqual(Page.objects.count(), 2)
        self.assertEqual(CMSPlugin.objects.count(), 4)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(
                "%s?copy_target=%s&language=%s" % (admin_reverse("cms_page_add_page_type"), page.pk, 'en'))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(Page.objects.count(), 3)
            self.assertEqual(Page.objects.filter(reverse_id="page_types").count(), 1)
            page_types = Page.objects.get(reverse_id='page_types')
            url = response.url if hasattr(response, 'url') else response['Location']
            expected_url_params = QueryDict(
                'target=%s&position=first-child&add_page_type=1&copy_target=%s&language=en' % (page_types.pk, page.pk))
            response_url_params = QueryDict(urlparse(url).query)
            self.assertDictEqual(expected_url_params, response_url_params)
            response = self.client.get("%s?copy_target=%s&language=%s" % (
                admin_reverse("cms_page_add_page_type"), page.pk, 'en'), follow=True)
            self.assertEqual(response.status_code, 200)

            # test no page types if no page types there
            response = self.client.get(admin_reverse('cms_page_add'))
            self.assertNotContains(response, "page_type")
            # create out first page type
            page_data = {
                'title': 'type1', 'slug': 'type1', '_save': 1, 'template': 'static.html', 'site': 1,
                'language': 'en'
            }
            response = self.client.post(
                "%s?target=%s&position=first-child&add_page_type=1&copy_target=%s&language=en" % (
                    URL_CMS_PAGE_ADD, page_types.pk, page.pk
                ), data=page_data)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(Page.objects.count(), 4)
            self.assertEqual(CMSPlugin.objects.count(), 6)
            response = self.client.get(admin_reverse('cms_page_add'))
            self.assertContains(response, "page_type")
            # no page types available if you use the copy_target
            response = self.client.get("%s?copy_target=%s&language=en" % (admin_reverse('cms_page_add'), page.pk))
            self.assertNotContains(response, "page_type")

    def test_render_edit_mode(self):
        from django.core.cache import cache

        cache.clear()
        create_page('Test', 'static.html', 'en', published=True)
        for placeholder in Placeholder.objects.all():
            add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')

        user = self.get_superuser()
        self.assertEqual(Placeholder.objects.all().count(), 4)
        with self.login_user_context(user):
            output = force_text(
                self.client.get(
                    '/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
                ).content
            )
            self.assertIn('<b>Test</b>', output)
            self.assertEqual(Placeholder.objects.all().count(), 9)
            self.assertEqual(StaticPlaceholder.objects.count(), 2)
            for placeholder in Placeholder.objects.all():
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
            create_page('Test%s' % i, 'col_two.html', 'en', published=True)
        for placeholder in Placeholder.objects.all():
            add_plugin(placeholder, TextPlugin, 'en', body='<b>Test</b>')

        user = self.get_superuser()
        with self.login_user_context(user):
            with self.assertNumQueries(FuzzyInt(18, 33)):
                force_text(self.client.get(URL_CMS_PAGE))

    def test_smart_link_published_pages(self):
        admin, staff_guy = self._get_guys()
        page_url = URL_CMS_PAGE_PUBLISHED  # Not sure how to achieve this with reverse...

        with self.login_user_context(staff_guy):
            multi_title_page = create_page('main_title', 'col_two.html', 'en', published=True,
                                           overwrite_url='overwritten_url',
                                           menu_title='menu_title')

            title = multi_title_page.get_title_obj()
            title.page_title = 'page_title'
            title.save()

            multi_title_page.save()
            publish_page(multi_title_page, admin, 'en')

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
                if DJANGO_1_7:
                    charset = response._charset
                else:
                    charset = response.charset

                text = smart_str(response.content, charset)

                foundcount = text.count(USER_NAME)
                # 2 forms contain usernames as options
                self.assertEqual(foundcount, 2,
                                 "Username %s appeared %s times in response.content, expected 2 times" % (
                                     USER_NAME, foundcount))
