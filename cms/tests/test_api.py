import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import PermissionDenied
from django.template import TemplateDoesNotExist
from django.test.testcases import TestCase
from djangocms_text_ckeditor.cms_plugins import TextPlugin
from djangocms_text_ckeditor.models import Text
from menus.menu_pool import menu_pool

from cms.api import (
    generate_valid_slug,
    create_page,
    create_title,
    _verify_plugin_type,
    assign_user_to_page,
    publish_page,
)
from cms.apphook_pool import apphook_pool
from cms.constants import REVISION_INITIAL_COMMENT, TEMPLATE_INHERITANCE_MAGIC
from cms.models.pagemodel import Page
from cms.models.titlemodels import Title
from cms.models.permissionmodels import GlobalPagePermission
from cms.plugin_base import CMSPluginBase
from cms.test_utils.util.menu_extender import TestMenu
from cms.test_utils.util.mock import AttributeObject
from cms.tests.test_apphooks import APP_MODULE, APP_NAME
from cms.utils.reversion_hacks import Revision


def _grant_page_permission(user, codename):
    content_type = ContentType.objects.get_by_natural_key('cms', 'page')
    perm = Permission.objects.get_or_create(codename='%s_page' % codename,
                                            content_type=content_type)[0]
    user.user_permissions.add(perm)


class PythonAPITests(TestCase):
    def _get_default_create_page_arguments(self):
        return {
            'title': 'Test',
            'template': 'nav_playground.html',
            'language': 'en'
        }

    def test_generate_valid_slug(self):
        title = "Hello Title"
        expected_slug = "hello-title"
        # empty db, it should just slugify
        slug = generate_valid_slug(title, None, 'en')
        self.assertEqual(slug, expected_slug)

    def test_generage_valid_slug_check_existing(self):
        title = "Hello Title"
        create_page(title, 'nav_playground.html', 'en')
        # second time with same title, it should append -1
        expected_slug = "hello-title-1"
        slug = generate_valid_slug(title, None, 'en')
        self.assertEqual(slug, expected_slug)

    def test_generage_valid_slug_check_parent(self):
        title = "Hello Title"
        page = create_page(title, 'nav_playground.html', 'en')
        # second time with same title, it should append -1
        expected_slug = "hello-title"
        slug = generate_valid_slug(title, page, 'en')
        self.assertEqual(slug, expected_slug)

    def test_generage_valid_slug_check_parent_existing(self):
        title = "Hello Title"
        page = create_page(title, 'nav_playground.html', 'en')
        create_page(title, 'nav_playground.html', 'en', parent=page)
        # second time with same title, it should append -1
        expected_slug = "hello-title-1"
        slug = generate_valid_slug(title, page, 'en')
        self.assertEqual(slug, expected_slug)

    def test_invalid_apphook_type(self):
        self.assertRaises(TypeError, create_page, apphook=1,
                          **self._get_default_create_page_arguments())

    def test_invalid_template(self):
        kwargs = self._get_default_create_page_arguments()
        kwargs['template'] = "not_valid.htm"
        with self.settings(CMS_TEMPLATES=[("not_valid.htm", "notvalid")]):
            self.assertRaises(TemplateDoesNotExist, create_page, **kwargs)
            kwargs['template'] = TEMPLATE_INHERITANCE_MAGIC
        create_page(**kwargs)

    def test_apphook_by_class(self):
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
        apphooks = (
            '%s.%s' % (APP_MODULE, APP_NAME),
        )

        with self.settings(CMS_APPHOOKS=apphooks):
            apphook_pool.clear()
            apphook = apphook_pool.get_apphook(APP_NAME)
            page = create_page(apphook=apphook,
                               **self._get_default_create_page_arguments())
            self.assertEqual(page.get_application_urls('en'), APP_NAME)

    def test_invalid_dates(self):
        self.assertRaises(AssertionError, create_page, publication_date=1,
                          **self._get_default_create_page_arguments())
        self.assertRaises(AssertionError, create_page, publication_end_date=1,
                          **self._get_default_create_page_arguments())

    def test_nav_extenders_invalid_type(self):
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'TestMenu': TestMenu}
        self.assertRaises(AssertionError, create_page, navigation_extenders=1,
                          **self._get_default_create_page_arguments())
        menu_pool.menus = self.old_menu

    def test_nav_extenders_invalid_menu(self):
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {}
        self.assertRaises(AssertionError, create_page,
                          navigation_extenders=TestMenu,
                          **self._get_default_create_page_arguments())
        menu_pool.menus = self.old_menu

    def test_nav_extenders_valid(self):
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'TestMenu': TestMenu}
        page = create_page(navigation_extenders='TestMenu',
                           **self._get_default_create_page_arguments())
        self.assertEqual(page.navigation_extenders, 'TestMenu')
        menu_pool.menus = self.old_menu

    def test_verify_plugin_type_invalid_type(self):
        self.assertRaises(TypeError, _verify_plugin_type, 1)

    def test_verify_plugin_type_string(self):
        plugin_model, plugin_type = _verify_plugin_type("TextPlugin")
        self.assertEqual(plugin_model, Text)
        self.assertEqual(plugin_type, 'TextPlugin')

    def test_verify_plugin_type_string_invalid(self):
        self.assertRaises(TypeError, _verify_plugin_type, "InvalidPlugin")

    def test_verify_plugin_type_plugin_class(self):
        plugin_model, plugin_type = _verify_plugin_type(TextPlugin)
        self.assertEqual(plugin_model, Text)
        self.assertEqual(plugin_type, 'TextPlugin')

    def test_verify_plugin_type_invalid_plugin_class(self):
        class InvalidPlugin(CMSPluginBase):
            model = Text

        self.assertRaises(AssertionError, _verify_plugin_type, InvalidPlugin)

    def test_assign_user_to_page_nothing(self):
        page = create_page(**self._get_default_create_page_arguments())
        user = get_user_model().objects.create_user(username='user', email='user@django-cms.org',
                                                    password='user')
        user.is_staff = True
        request = AttributeObject(user=user)
        self.assertFalse(page.has_change_permission(request))

    def test_assign_user_to_page_single(self):
        page = create_page(**self._get_default_create_page_arguments())
        user = get_user_model().objects.create_user(username='user', email='user@django-cms.org',
                                                    password='user')
        user.is_staff = True
        user.save()
        request = AttributeObject(user=user)
        assign_user_to_page(page, user, can_change=True)
        self.assertFalse(page.has_change_permission(request))
        self.assertFalse(page.has_add_permission(request))
        _grant_page_permission(user, 'change')
        page = Page.objects.get(pk=page.pk)
        user = get_user_model().objects.get(pk=user.pk)
        request = AttributeObject(user=user)
        self.assertTrue(page.has_change_permission(request))
        self.assertFalse(page.has_add_permission(request))

    def test_assign_user_to_page_all(self):
        page = create_page(**self._get_default_create_page_arguments())
        user = get_user_model().objects.create_user(username='user', email='user@django-cms.org',
                                                    password='user')
        user.is_staff = True
        user.save()
        request = AttributeObject(user=user)
        assign_user_to_page(page, user, grant_all=True)
        self.assertFalse(page.has_change_permission(request))
        self.assertTrue(page.has_add_permission(request))
        _grant_page_permission(user, 'change')
        _grant_page_permission(user, 'add')
        page = Page.objects.get(pk=page.pk)
        user = get_user_model().objects.get(pk=user.pk)
        request = AttributeObject(user=user)
        self.assertTrue(page.has_change_permission(request))
        self.assertTrue(page.has_add_permission(request))

    def test_page_overwrite_url_default(self):
        self.assertEqual(Page.objects.all().count(), 0)
        home = create_page('home', 'nav_playground.html', 'en', published=True)
        self.assertTrue(home.is_published('en', True))
        self.assertTrue(home.is_home)
        page = create_page(**self._get_default_create_page_arguments())
        self.assertFalse(page.is_home)
        self.assertFalse(page.get_title_obj_attribute('has_url_overwrite'))
        self.assertEqual(page.get_title_obj_attribute('path'), 'test')

    def test_create_page_can_overwrite_url(self):
        page_attrs = self._get_default_create_page_arguments()
        page_attrs["overwrite_url"] = 'test/home'
        page = create_page(**page_attrs)
        self.assertTrue(page.get_title_obj_attribute('has_url_overwrite'))
        self.assertEqual(page.get_title_obj_attribute('path'), 'test/home')

    def test_create_reverse_id_collision(self):
        create_page('home', 'nav_playground.html', 'en', published=True, reverse_id="foo")
        self.assertRaises(FieldError, create_page, 'foo', 'nav_playground.html', 'en', published=True, reverse_id="foo")
        self.assertTrue(Page.objects.count(), 2)

    def test_publish_page(self):
        page_attrs = self._get_default_create_page_arguments()
        page_attrs['language'] = 'en'
        page_attrs['published'] = False
        page = create_page(**page_attrs)
        self.assertFalse(page.is_published('en'))
        self.assertEqual(page.changed_by, 'script')
        user = get_user_model().objects.create_user(username='user', email='user@django-cms.org',
                                                    password='user')
        # Initially no permission
        self.assertRaises(PermissionDenied, publish_page, page, user, 'en')
        user.is_staff = True
        user.save()
        # Permissions are cached on user instances, so create a new one.
        user = get_user_model().objects.get(pk=user.pk)
        _grant_page_permission(user, 'publish')
        gpp = GlobalPagePermission.objects.create(user=user, can_publish=True)
        gpp.sites.add(page.site)
        publish_page(page, user, 'en')
        # Reload the page to get updates.
        page = page.reload()
        self.assertTrue(page.is_published('en'))
        self.assertEqual(page.changed_by, user.get_username())

    def test_create_with_revision(self):
        page_c_type = ContentType.objects.get_for_model(Page)

        user = get_user_model().objects.create_user(
            username='user',
            email='user@django-cms.org',
            password='user',
        )

        page_attrs = self._get_default_create_page_arguments()
        page_attrs['language'] = 'en'
        page_attrs['created_by'] = user
        page_attrs['with_revision'] = True

        page = create_page(**page_attrs)

        latest_revision = Revision.objects.latest('pk')
        versions = (
            latest_revision
            .version_set
            .filter(content_type=page_c_type, object_id_int=page.pk)
        )

        # assert a new version for the page has been created
        self.assertEqual(1, versions.count())

        # assert revision comment was set correctly
        self.assertEqual(
            latest_revision.comment,
            REVISION_INITIAL_COMMENT,
        )

        # assert revision user was set correctly
        self.assertEqual(
            latest_revision.user_id,
            user.pk,
        )

        title_c_type = ContentType.objects.get_for_model(Title)
        title = create_title('de', 'test de', page, with_revision=True)

        latest_revision = Revision.objects.latest('pk')
        versions = (
            latest_revision
            .version_set
            .filter(content_type=title_c_type, object_id_int=title.pk)
        )

        # assert a new version for the title has been created
        self.assertEqual(1, versions.count())

    def test_create_with_revision_fail(self):
        # tests that we're unable to create a page or title
        # through the api with the revision option if reversion
        # is not installed.
        page_attrs = self._get_default_create_page_arguments()
        page_attrs['language'] = 'en'
        page_attrs['with_revision'] = True

        apps = list(settings.INSTALLED_APPS)
        apps.remove('reversion')

        with self.settings(INSTALLED_APPS=apps):
            with self.assertRaises(ImproperlyConfigured):
                create_page(**page_attrs)

        page = create_page(**page_attrs)

        with self.settings(INSTALLED_APPS=apps):
            with self.assertRaises(ImproperlyConfigured):
                create_title('de', 'test de', page, with_revision=True)
