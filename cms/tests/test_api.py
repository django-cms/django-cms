import sys

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError, PermissionDenied
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from djangocms_text_ckeditor.cms_plugins import TextPlugin
from djangocms_text_ckeditor.models import Text

from cms.api import _verify_plugin_type, assign_user_to_page, create_page, publish_page
from cms.apphook_pool import apphook_pool
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models.pagemodel import Page
from cms.models.permissionmodels import GlobalPagePermission
from cms.plugin_base import CMSPluginBase
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.menu_extender import TestMenu
from cms.tests.test_apphooks import APP_MODULE, APP_NAME
from menus.menu_pool import menu_pool


def _grant_page_permission(user, codename):
    content_type = ContentType.objects.get_by_natural_key('cms', 'page')
    perm = Permission.objects.get_or_create(codename='%s_page' % codename,
                                            content_type=content_type)[0]
    user.user_permissions.add(perm)


class PythonAPITests(CMSTestCase):
    def _get_default_create_page_arguments(self):
        return {
            'title': 'Test',
            'template': 'nav_playground.html',
            'language': 'en'
        }

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
            f'{APP_MODULE}.{APP_NAME}',
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
        self.assertFalse(page.has_change_permission(user))

    def test_assign_user_to_page_single(self):
        page = create_page(**self._get_default_create_page_arguments())
        user = get_user_model().objects.create_user(username='user', email='user@django-cms.org',
                                                    password='user')
        user.is_staff = True
        user.save()
        assign_user_to_page(page, user, can_change=True)
        self.assertFalse(page.has_change_permission(user))
        self.assertFalse(page.has_add_permission(user))
        _grant_page_permission(user, 'change')
        page = Page.objects.get(pk=page.pk)
        user = get_user_model().objects.get(pk=user.pk)
        self.assertTrue(page.has_change_permission(user))
        self.assertFalse(page.has_add_permission(user))

    def test_assign_user_to_page_all(self):
        page = create_page(**self._get_default_create_page_arguments())
        user = get_user_model().objects.create_user(username='user', email='user@django-cms.org',
                                                    password='user')
        user.is_staff = True
        user.save()
        assign_user_to_page(page, user, grant_all=True)
        self.assertFalse(page.has_change_permission(user))
        self.assertFalse(page.has_add_permission(user))
        _grant_page_permission(user, 'change')
        _grant_page_permission(user, 'add')
        page = Page.objects.get(pk=page.pk)
        user = get_user_model().objects.get(pk=user.pk)
        self.assertTrue(page.has_change_permission(user))
        self.assertTrue(page.has_add_permission(user))

    def test_page_overwrite_url_default(self):
        self.assertEqual(Page.objects.all().count(), 0)
        home = create_page('root', 'nav_playground.html', 'en', published=True)
        self.assertTrue(home.is_published('en', True))
        self.assertFalse(home.is_home)
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

    def test_create_page_atomic(self):
        # Ref: https://github.com/divio/django-cms/issues/5652
        # We'll simulate a scenario where a user creates a page with an
        # invalid template which causes Django to throw an error when the
        # template is scanned for placeholders and thus short circuits the
        # creation mechanism.
        page_attrs = self._get_default_create_page_arguments()

        # It's important to use TEMPLATE_INHERITANCE_MAGIC to avoid the cms
        # from loading the template before saving and triggering the template error
        # Instead, we delay the loading of the template until after the save is executed.
        page_attrs["template"] = TEMPLATE_INHERITANCE_MAGIC

        self.assertFalse(Page.objects.filter(template=TEMPLATE_INHERITANCE_MAGIC).exists())

        with self.settings(CMS_TEMPLATES=[("col_invalid.html", "notvalid")]):
            self.assertRaises(TemplateSyntaxError, create_page, **page_attrs)
            # The template raised an exception which should cause the database to roll back
            # instead of committing a page in a partial state.
            self.assertFalse(Page.objects.filter(template=TEMPLATE_INHERITANCE_MAGIC).exists())

    def test_create_reverse_id_collision(self):
        create_page('home', 'nav_playground.html', 'en', published=True, reverse_id="foo")
        self.assertRaises(FieldError, create_page, 'foo', 'nav_playground.html', 'en', published=True, reverse_id="foo")
        self.assertEqual(Page.objects.count(), 2)

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

        self.add_permission(user, 'change_page')
        self.add_permission(user, 'publish_page')

        gpp = GlobalPagePermission.objects.create(user=user, can_change=True, can_publish=True)
        gpp.sites.add(page.node.site)
        publish_page(page, user, 'en')
        # Reload the page to get updates.
        page = page.reload()
        self.assertTrue(page.is_published('en'))
        self.assertEqual(page.changed_by, user.get_username())

    def test_create_page_assert_parent_is_draft(self):
        page_attrs = self._get_default_create_page_arguments()
        page_attrs['published'] = True
        parent_page = create_page(**page_attrs)
        parent_page_public = parent_page.get_public_object()
        self.assertRaises(AssertionError, create_page, parent=parent_page_public, **page_attrs)

    def test_create_page_page_title(self):
        page = create_page(**dict(self._get_default_create_page_arguments(), page_title='page title'))
        self.assertEqual(page.get_title_obj_attribute('page_title'), 'page title')

    def test_create_page_with_position_regression_6345(self):
        # ref: https://github.com/divio/django-cms/issues/6345
        parent = create_page('p', 'nav_playground.html', 'en')
        rightmost = create_page('r', 'nav_playground.html', 'en', parent=parent)
        leftmost = create_page('l', 'nav_playground.html', 'en', parent=rightmost, position='left')
        create_page('m', 'nav_playground.html', 'en', parent=leftmost, position='right')
        children_titles = list(p.get_title('de') for p in parent.get_child_pages())
        self.assertEqual(children_titles, ['l', 'm', 'r'])
