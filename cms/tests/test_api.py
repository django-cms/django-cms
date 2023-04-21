import sys

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from djangocms_text_ckeditor.cms_plugins import TextPlugin
from djangocms_text_ckeditor.models import Text

from cms.api import (
    _verify_plugin_type,
    add_plugin,
    assign_user_to_page,
    create_page,
)
from cms.apphook_pool import apphook_pool
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page, Placeholder
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
            '%s.%s' % (APP_MODULE, APP_NAME),
        )

        with self.settings(CMS_APPHOOKS=apphooks):
            apphook_pool.clear()
            apphook = apphook_pool.get_apphook(APP_NAME)
            page = create_page(apphook=apphook,
                               **self._get_default_create_page_arguments())
            self.assertEqual(page.get_application_urls('en'), APP_NAME)

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
        home = create_page('root', 'nav_playground.html', 'en')
        self.assertFalse(home.is_home)
        page = create_page(**self._get_default_create_page_arguments())
        self.assertFalse(page.is_home)
        self.assertTrue(page.get_urls().filter(path='test', managed=True).exists())

    def test_create_page_can_overwrite_url(self):
        page_attrs = self._get_default_create_page_arguments()
        page_attrs["overwrite_url"] = 'test/home'
        page = create_page(**page_attrs)
        self.assertTrue(page.get_urls().filter(path='test/home', managed=False).exists())

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

        self.assertFalse(Page.objects.filter(pagecontent_set__template=TEMPLATE_INHERITANCE_MAGIC).exists())

        with self.settings(CMS_TEMPLATES=[("col_invalid.html", "notvalid")]):
            self.assertRaises(TemplateSyntaxError, create_page, **page_attrs)
            # The template raised an exception which should cause the database to roll back
            # instead of committing a page in a partial state.
            self.assertFalse(Page.objects.filter(pagecontent_set__template=TEMPLATE_INHERITANCE_MAGIC).exists())

    def test_create_reverse_id_collision(self):
        create_page('home', 'nav_playground.html', 'en', reverse_id="foo")
        self.assertRaises(FieldError, create_page, 'foo', 'nav_playground.html', 'en', reverse_id="foo")
        self.assertTrue(Page.objects.count(), 2)


class PythonAPIPluginTests(CMSTestCase):

    def setUp(self):
        self.placeholder = Placeholder.objects.create(slot='main')

    def test_add_root_plugin(self):
        root_plugin_1 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en')
        self.assertEqual(root_plugin_1.position, 1)
        self.assertEqual(root_plugin_1.language, 'en')
        self.assertEqual(root_plugin_1.plugin_type, 'SolarSystemPlugin')

    def test_add_root_plugin_first(self):
        """
        User can add a new plugin to be in the first position
        """
        root_plugin_2 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en')
        root_plugin_3 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en', position='last-child')
        root_plugin_1 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en', position='first-child')
        new_tree = self.placeholder.get_plugins('en').values_list('pk', 'position')
        expected = [(root_plugin_1.pk, 1), (root_plugin_2.pk, 2), (root_plugin_3.pk, 3)]
        self.assertSequenceEqual(new_tree, expected)

    def test_add_root_plugin_middle(self):
        root_plugin_1 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en')
        root_plugin_2 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en', position='last-child')
        root_plugin_4 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en', position='last-child')
        root_plugin_6 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en', position='last-child')
        root_plugin_3 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en', position='left', target=root_plugin_4)
        root_plugin_5 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='right', target=root_plugin_4.reload()
        )
        new_tree = self.placeholder.get_plugins('en').values_list('pk', 'position')
        expected = [
            (root_plugin_1.pk, 1),
            (root_plugin_2.pk, 2),
            (root_plugin_3.pk, 3),
            (root_plugin_4.pk, 4),
            (root_plugin_5.pk, 5),
            (root_plugin_6.pk, 6),
        ]
        self.assertSequenceEqual(new_tree, expected)

    def test_add_child_plugin(self):
        root_plugin_1 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en')
        child_plugin_1 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en', target=root_plugin_1)
        self.assertEqual(child_plugin_1.position, 2)
        self.assertEqual(child_plugin_1.parent_id, root_plugin_1.pk)
        self.assertEqual(child_plugin_1.language, 'en')
        self.assertEqual(child_plugin_1.plugin_type, 'SolarSystemPlugin')

    def test_add_child_plugin_first(self):
        """
        User can add a new plugin to be in the first position
        """
        root_plugin_1 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en')
        child_plugin_2 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='last-child', target=root_plugin_1
        )
        child_plugin_3 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='last-child', target=root_plugin_1
        )
        child_plugin_1 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='first-child', target=root_plugin_1
        )
        root_plugin_2 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en')
        new_tree = self.placeholder.get_plugins('en').values_list('pk', 'position')
        expected = [
            (root_plugin_1.pk, 1),
            (child_plugin_1.pk, 2),
            (child_plugin_2.pk, 3),
            (child_plugin_3.pk, 4),
            (root_plugin_2.pk, 5),
        ]
        self.assertSequenceEqual(new_tree, expected)

    def test_add_child_plugin_middle(self):
        root_plugin_1 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en')
        child_plugin_1 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='last-child', target=root_plugin_1
        )
        child_plugin_2 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='last-child', target=root_plugin_1
        )
        child_plugin_4 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='last-child', target=root_plugin_1
        )
        child_plugin_6 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='last-child', target=root_plugin_1
        )
        child_plugin_3 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='left', target=child_plugin_4
        )
        child_plugin_5 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='right', target=child_plugin_4.reload()
        )
        root_plugin_3 = add_plugin(self.placeholder, 'SolarSystemPlugin', 'en', position='last-child')
        new_tree = self.placeholder.get_plugins('en').values_list('pk', 'position')
        expected = [
            (root_plugin_1.pk, 1),
            (child_plugin_1.pk, 2),
            (child_plugin_2.pk, 3),
            (child_plugin_3.pk, 4),
            (child_plugin_4.pk, 5),
            (child_plugin_5.pk, 6),
            (child_plugin_6.pk, 7),
            (root_plugin_3.pk, 8),
        ]
        self.assertSequenceEqual(new_tree, expected)

        # Insert additional plugin right of first root plugin to see where it is positioned relative to the
        # first root plugin's children
        root_plugin_2 = add_plugin(
            self.placeholder, 'SolarSystemPlugin', 'en', position='right', target=root_plugin_1
        )
        new_tree = self.placeholder.get_plugins('en').values_list('pk', 'position')
        expected = [
            (root_plugin_1.pk, 1),
            (child_plugin_1.pk, 2),
            (child_plugin_2.pk, 3),
            (child_plugin_3.pk, 4),
            (child_plugin_4.pk, 5),
            (child_plugin_5.pk, 6),
            (child_plugin_6.pk, 7),
            (root_plugin_2.pk, 8),
            (root_plugin_3.pk, 9),
        ]
        self.assertSequenceEqual(new_tree, expected)
