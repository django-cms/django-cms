# -*- coding: utf-8 -*-
import json
import sys
import warnings

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.template import engines
from django.template.context import Context
from django.test import testcases
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.six.moves.urllib.parse import unquote, urljoin
from django.utils.timezone import now
from django.utils.translation import activate
from menus.menu_pool import menu_pool

from cms.api import create_page
from cms.constants import (
    PUBLISHER_STATE_DEFAULT,
    PUBLISHER_STATE_DIRTY,
    PUBLISHER_STATE_PENDING,
)
from cms.plugin_rendering import ContentRenderer, StructureRenderer
from cms.models import Page
from cms.models.permissionmodels import (
    GlobalPagePermission,
    PagePermission,
    PageUser,
)
from cms.test_utils.util.context_managers import UserLoginContext
from cms.utils.conf import get_cms_setting
from cms.utils.permissions import set_current_user
from cms.utils.urlutils import admin_reverse


URL_CMS_PAGE = "/en/admin/cms/page/"
URL_CMS_PAGE_ADD = urljoin(URL_CMS_PAGE, "add/")
URL_CMS_PAGE_CHANGE_BASE = urljoin(URL_CMS_PAGE, "%d/")
URL_CMS_PAGE_CHANGE = urljoin(URL_CMS_PAGE_CHANGE_BASE, "change/")
URL_CMS_PAGE_ADVANCED_CHANGE = urljoin(URL_CMS_PAGE, "%d/advanced-settings/")
URL_CMS_PAGE_PERMISSION_CHANGE = urljoin(URL_CMS_PAGE, "%d/permission-settings/")
URL_CMS_PAGE_PERMISSIONS = urljoin(URL_CMS_PAGE, "%d/permissions/")
URL_CMS_PAGE_PUBLISHED = urljoin(URL_CMS_PAGE, "published-pages/")
URL_CMS_PAGE_MOVE = urljoin(URL_CMS_PAGE, "%d/move-page/")
URL_CMS_PAGE_COPY = urljoin(URL_CMS_PAGE, "%d/copy-page/")
URL_CMS_PAGE_CHANGE_LANGUAGE = URL_CMS_PAGE_CHANGE + "?language=%s"
URL_CMS_PAGE_CHANGE_TEMPLATE = urljoin(URL_CMS_PAGE_CHANGE, "change-template/")
URL_CMS_PAGE_PUBLISH = urljoin(URL_CMS_PAGE_CHANGE_BASE, "%s/publish/")
URL_CMS_PAGE_DELETE = urljoin(URL_CMS_PAGE_CHANGE_BASE, "delete/")
URL_CMS_PLUGIN_ADD = urljoin(URL_CMS_PAGE, "add-plugin/")
URL_CMS_PLUGIN_EDIT = urljoin(URL_CMS_PAGE, "edit-plugin/")
URL_CMS_PLUGIN_MOVE = urljoin(URL_CMS_PAGE, "move-plugin/")
URL_CMS_PLUGIN_PAGE_MOVE = urljoin(URL_CMS_PAGE_CHANGE_BASE, "move-plugin/")
URL_CMS_PLUGIN_PAGE_ADD = urljoin(URL_CMS_PAGE_CHANGE_BASE, "add-plugin/")
URL_CMS_PLUGIN_REMOVE = urljoin(URL_CMS_PAGE, "delete-plugin/")
URL_CMS_PLUGIN_DELETE = urljoin(URL_CMS_PAGE, "delete-plugin/%s/")
URL_CMS_PLUGINS_COPY = urljoin(URL_CMS_PAGE, "copy-plugins/")
URL_CMS_TRANSLATION_DELETE = urljoin(URL_CMS_PAGE_CHANGE_BASE, "delete-translation/")
URL_CMS_USERSETTINGS = "/en/admin/cms/usersettings/"


class _Warning(object):
    def __init__(self, message, category, filename, lineno):
        self.message = message
        self.category = category
        self.filename = filename
        self.lineno = lineno


def _collectWarnings(observeWarning, f, *args, **kwargs):
    def showWarning(message, category, filename, lineno, file=None, line=None):
        assert isinstance(message, Warning)
        observeWarning(_Warning(
            message.args[0], category, filename, lineno))

    # Disable the per-module cache for every module otherwise if the warning
    # which the caller is expecting us to collect was already emitted it won't
    # be re-emitted by the call to f which happens below.
    for v in sys.modules.values():
        if v is not None:
            try:
                v.__warningregistry__ = None
            except:
                # Don't specify a particular exception type to handle in case
                # some wacky object raises some wacky exception in response to
                # the setattr attempt.
                pass

    origFilters = warnings.filters[:]
    origShow = warnings.showwarning
    warnings.simplefilter('always')
    try:
        warnings.showwarning = showWarning
        result = f(*args, **kwargs)
    finally:
        warnings.filters[:] = origFilters
        warnings.showwarning = origShow
    return result


class BaseCMSTestCase(object):
    counter = 1

    def _fixture_setup(self):
        super(BaseCMSTestCase, self)._fixture_setup()
        self.create_fixtures()
        activate("en")

    def create_fixtures(self):
        pass

    def _post_teardown(self):
        menu_pool.clear()
        cache.clear()
        super(BaseCMSTestCase, self)._post_teardown()
        set_current_user(None)

    def login_user_context(self, user):
        return UserLoginContext(self, user)

    def get_permission(self, codename):
        return Permission.objects.get(codename=codename)

    def add_permission(self, user, codename):
        user.user_permissions.add(self.get_permission(codename))

    def remove_permission(self, user, codename):
        user.user_permissions.remove(Permission.objects.get(codename=codename))

    def add_global_permission(self, user, **kwargs):
        options = {
            'can_add': False,
            'can_change': False,
            'can_delete': False,
            'can_change_advanced_settings': False,
            'can_publish': False,
            'can_change_permissions': False,
            'can_move_page': False,
            'can_recover_page': False,
            'user': user,
        }
        options.update(**kwargs)

        gpp = GlobalPagePermission.objects.create(**options)
        gpp.sites.set(Site.objects.all())
        return gpp

    def add_page_permission(self, user, page, **kwargs):
        options = {
            'can_add': False,
            'can_change': False,
            'can_delete': False,
            'can_change_advanced_settings': False,
            'can_publish': False,
            'can_change_permissions': False,
            'can_move_page': False,
            'page': page,
            'user': user,
        }
        options.update(**kwargs)

        pp = PagePermission.objects.create(**options)
        pp.sites = Site.objects.all()
        return pp

    def _create_user(self, username, is_staff=False, is_superuser=False,
                     is_active=True, add_default_permissions=False, permissions=None):
        """
        Use this method to create users.

        Default permissions on page and text plugin are added if creating a
        non-superuser and `add_default_permissions` is set.

        Set `permissions` parameter to an iterable of permission codes to add
        custom permissios.
        """
        User = get_user_model()

        fields = dict(email=username + '@django-cms.org', last_login=now(),
                      is_staff=is_staff, is_active=is_active, is_superuser=is_superuser
        )

        # Check for special case where email is used as username
        if (get_user_model().USERNAME_FIELD != 'email'):
            fields[get_user_model().USERNAME_FIELD] = username

        user = User(**fields)

        user.set_password(getattr(user, get_user_model().USERNAME_FIELD))
        user.save()
        if is_staff and not is_superuser and add_default_permissions:
            user.user_permissions.add(Permission.objects.get(codename='add_text'))
            user.user_permissions.add(Permission.objects.get(codename='delete_text'))
            user.user_permissions.add(Permission.objects.get(codename='change_text'))
            user.user_permissions.add(Permission.objects.get(codename='publish_page'))

            user.user_permissions.add(Permission.objects.get(codename='add_page'))
            user.user_permissions.add(Permission.objects.get(codename='change_page'))
            user.user_permissions.add(Permission.objects.get(codename='delete_page'))
        if is_staff and not is_superuser and permissions:
            for permission in permissions:
                user.user_permissions.add(Permission.objects.get(codename=permission))
        return user

    def get_superuser(self):
        try:
            query = dict()

            if get_user_model().USERNAME_FIELD != "email":
                query[get_user_model().USERNAME_FIELD] = "admin"
            else:
                query[get_user_model().USERNAME_FIELD] = "admin@django-cms.org"

            admin = get_user_model().objects.get(**query)
        except get_user_model().DoesNotExist:
            admin = self._create_user("admin", is_staff=True, is_superuser=True)
        return admin

    def get_staff_user_with_no_permissions(self):
        """
        Used in security tests
        """
        staff = self._create_user("staff", is_staff=True, is_superuser=False)
        return staff

    def get_staff_user_with_std_permissions(self):
        """
        This is a non superuser staff
        """
        staff = self._create_user("staff", is_staff=True, is_superuser=False,
                                  add_default_permissions=True)
        return staff

    def get_standard_user(self):
        """
        Used in security tests
        """
        standard = self._create_user("standard", is_staff=False, is_superuser=False)
        return standard

    def get_staff_page_user(self, created_by=None):
        if not created_by:
            created_by = self.get_superuser()

        parent_link_field = list(PageUser._meta.parents.values())[0]
        user = self._create_user(
            'perms-testuser',
            is_staff=True,
            is_superuser=False,
        )
        data = model_to_dict(user, exclude=['groups', 'user_permissions'])
        data[parent_link_field.name] = user
        data['created_by'] = created_by
        return PageUser.objects.create(**data)

    def get_new_page_data(self, parent_id=''):
        page_data = {
            'title': 'test page %d' % self.counter,
            'slug': 'test-page-%d' % self.counter,
            'parent_node': parent_id,
        }
        # required only if user haves can_change_permission
        self.counter += 1
        return page_data

    def get_new_page_data_dbfields(self, parent=None, site=None,
                                   language=None,
                                   template='nav_playground.html', ):
        page_data = {
            'title': 'test page %d' % self.counter,
            'slug': 'test-page-%d' % self.counter,
            'language': settings.LANGUAGES[0][0] if not language else language,
            'template': template,
            'parent': parent if parent else None,
            'site': site if site else Site.objects.get_current(),
        }
        self.counter = self.counter + 1
        return page_data

    def get_pagedata_from_dbfields(self, page_data):
        """Converts data created by get_new_page_data_dbfields to data
        created from get_new_page_data so you can switch between test cases
        in api.create_page and client.post"""
        page_data['site'] = page_data['site'].id
        page_data['parent'] = page_data['parent'].id if page_data['parent'] else ''
        # required only if user haves can_change_permission
        page_data['pagepermission_set-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-MAX_NUM_FORMS'] = 0
        page_data['pagepermission_set-2-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-2-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-2-MAX_NUM_FORMS'] = 0
        return page_data

    def print_page_structure(self, qs):
        """Just a helper to see the page struct.
        """
        for page in qs.order_by('path'):
            ident = "  " * page.level
            print(u"%s%s (%s), path: %s, depth: %s, numchild: %s" % (ident, page,
            page.pk, page.path, page.depth, page.numchild))

    def print_node_structure(self, nodes, *extra):
        def _rec(nodes, level=0):
            ident = level * '  '
            for node in nodes:
                raw_attrs = [(bit, getattr(node, bit, node.attr.get(bit, "unknown"))) for bit in extra]
                attrs = ', '.join(['%s: %r' % data for data in raw_attrs])
                print(u"%s%s: %s" % (ident, node.title, attrs))
                _rec(node.children, level + 1)

        _rec(nodes)

    def assertObjectExist(self, qs, **filter):
        try:
            return qs.get(**filter)
        except ObjectDoesNotExist:
            pass
        raise self.failureException("ObjectDoesNotExist raised for filter %s" % filter)

    def assertObjectDoesNotExist(self, qs, **filter):
        try:
            qs.get(**filter)
        except ObjectDoesNotExist:
            return
        raise self.failureException("ObjectDoesNotExist not raised for filter %s" % filter)

    def copy_page(self, page, target_page, position=0, target_site=None):
        from cms.utils.page import get_available_slug

        if target_site is None:
            target_site = target_page.node.site

        data = {
            'position': position,
            'target': target_page.pk,
            'source_site': page.node.site_id,
            'copy_permissions': 'on',
            'copy_moderation': 'on',
        }
        source_translation = page.title_set.all()[0]
        parent_translation = target_page.title_set.all()[0]
        language = source_translation.language
        copied_page_path = source_translation.get_path_for_base(parent_translation.path)
        new_page_slug = get_available_slug(target_site, copied_page_path, language)

        with self.settings(SITE_ID=target_site.pk):
            response = self.client.post(URL_CMS_PAGE + "%d/copy-page/" % page.pk, data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf8'))
        copied_page = self.assertObjectExist(
            Page.objects.all(),
            pk=response_data['id'],
        )
        self.assertObjectExist(copied_page.title_set.filter(language=language), slug=new_page_slug)
        page._clear_node_cache()
        target_page._clear_node_cache()
        return copied_page

    def create_homepage(self, *args, **kwargs):
        homepage = create_page(*args, **kwargs)
        homepage.set_as_homepage()
        return homepage.reload()

    def move_page(self, page, target_page, position="first-child"):
        page.move_page(target_page.node, position)
        return self.reload_page(page)

    def reload_page(self, page):
        """
        Returns a fresh instance of the page from the database
        """
        return self.reload(page)

    def reload(self, obj):
        return obj.__class__.objects.get(pk=obj.pk)

    def get_pages_root(self):
        return unquote(reverse("pages-root"))

    def get_context(self, path=None, page=None):
        if not path:
            path = self.get_pages_root()
        context = {}
        request = self.get_request(path, page=page)
        context['request'] = request
        return Context(context)

    def get_content_renderer(self, request=None):
        request = request or self.get_request()
        return ContentRenderer(request)

    def get_structure_renderer(self, request=None):
        request = request or self.get_request()
        return StructureRenderer(request)

    def get_request(self, path=None, language=None, post_data=None, enforce_csrf_checks=False, page=None):
        factory = RequestFactory()

        if not path:
            path = self.get_pages_root()

        if not language:
            if settings.USE_I18N:
                language = settings.LANGUAGES[0][0]
            else:
                language = settings.LANGUAGE_CODE

        if post_data:
            request = factory.post(path, post_data)
        else:
            request = factory.get(path)
        request.session = self.client.session
        request.user = getattr(self, 'user', AnonymousUser())
        request.LANGUAGE_CODE = language
        request._dont_enforce_csrf_checks = not enforce_csrf_checks
        if page:
            request.current_page = page
        else:
            request.current_page = None

        class MockStorage(object):

            def __len__(self):
                return 0

            def __iter__(self):
                return iter([])

            def add(self, level, message, extra_tags=''):
                pass

            def update(self, response):
                pass

        request._messages = MockStorage()
        return request

    def failUnlessWarns(self, category, message, f, *args, **kwargs):
        warningsShown = []
        result = _collectWarnings(warningsShown.append, f, *args, **kwargs)

        if not warningsShown:
            self.fail("No warnings emitted")
        first = warningsShown[0]
        for other in warningsShown[1:]:
            if ((other.message, other.category)
                != (first.message, first.category)):
                self.fail("Can't handle different warnings")
        self.assertEqual(first.message, message)
        self.assertTrue(first.category is category)

        return result

    assertWarns = failUnlessWarns

    def load_template_from_string(self, template):
        return engines['django'].from_string(template)

    def get_template(self, template):
        return engines['django'].get_template(template)

    def render_template_obj(self, template, context, request):
        template_obj = self.load_template_from_string(template)
        return template_obj.render(context, request)

    def apphook_clear(self):
        from cms.apphook_pool import apphook_pool
        for name, label in list(apphook_pool.get_apphooks()):
            if apphook_pool.apps[name].__class__.__module__ in sys.modules:
                del sys.modules[apphook_pool.apps[name].__class__.__module__]
        apphook_pool.clear()

    def get_admin_url(self, model, action, *args):
        opts = model._meta
        url_name = "{}_{}_{}".format(opts.app_label, opts.model_name, action)
        return admin_reverse(url_name, args=args)

    def get_permissions_test_page(self):
        admin = self.get_superuser()
        create_page(
            "home",
            "nav_playground.html",
            "en",
            created_by=admin,
            published=True,
        )
        page = create_page(
            "permissions",
            "nav_playground.html",
            "en",
            created_by=admin,
            published=True,
            reverse_id='permissions',
        )
        return page

    def get_plugin_model(self, plugin_type):
        from cms.plugin_pool import plugin_pool

        return plugin_pool.get_plugin(plugin_type).model

    def get_add_plugin_uri(self, placeholder, plugin_type, language='en', parent=None):
        if placeholder.page:
            path = placeholder.page.get_absolute_url(language)
        else:
            path = '/{}/'.format(language)

        endpoint = placeholder.get_add_url()
        data = {
            'plugin_type': plugin_type,
            'placeholder_id': placeholder.pk,
            'plugin_language': language,
            'cms_path': path,
        }

        if parent:
            data['plugin_parent'] = parent.pk
        return endpoint + '?' + urlencode(data)

    def get_change_plugin_uri(self, plugin, container=None, language=None):
        container = container or Page
        language = language or 'en'

        if plugin.page:
            path = plugin.page.get_absolute_url(language)
        else:
            path = '/{}/'.format(language)

        endpoint = self.get_admin_url(container, 'edit_plugin', plugin.pk)
        endpoint += '?' + urlencode({'cms_path': path})
        return endpoint

    def get_move_plugin_uri(self, plugin, container=None, language=None):
        container = container or Page
        language = language or 'en'

        if plugin.page:
            path = plugin.page.get_absolute_url(language)
        else:
            path = '/{}/'.format(language)

        endpoint = self.get_admin_url(container, 'move_plugin')
        endpoint += '?' + urlencode({'cms_path': path})
        return endpoint

    def get_copy_plugin_uri(self, plugin, container=None, language=None):
        container = container or Page
        language = language or 'en'

        if plugin.page:
            path = plugin.page.get_absolute_url(language)
        else:
            path = '/{}/'.format(language)

        endpoint = self.get_admin_url(container, 'copy_plugins')
        endpoint += '?' + urlencode({'cms_path': path})
        return endpoint

    def get_copy_placeholder_uri(self, placeholder, container=None, language=None):
        container = container or Page
        language = language or 'en'

        if placeholder.page:
            path = placeholder.page.get_absolute_url(language)
        else:
            path = '/{}/'.format(language)

        endpoint = self.get_admin_url(container, 'copy_plugins')
        endpoint += '?' + urlencode({'cms_path': path})
        return endpoint

    def get_delete_plugin_uri(self, plugin, container=None, language=None):
        container = container or Page
        language = language or 'en'

        if plugin.page:
            path = plugin.page.get_absolute_url(language)
        else:
            path = '/{}/'.format(language)

        endpoint = self.get_admin_url(container, 'delete_plugin', plugin.pk)
        endpoint += '?' + urlencode({'cms_path': path})
        return endpoint

    def get_clear_placeholder_url(self, placeholder, container=None, language=None):
        container = container or Page
        language = language or 'en'

        if placeholder.page:
            path = placeholder.page.get_absolute_url(language)
        else:
            path = '/{}/'.format(language)

        endpoint = self.get_admin_url(
            container,
            'clear_placeholder',
            placeholder.pk,
        )
        endpoint += '?' + urlencode({
            'language': language,
            'cms_path': path,
        })
        return endpoint

    def get_edit_on_url(self, url):
        return '{}?{}'.format(url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))

    def get_edit_off_url(self, url):
        return '{}?{}'.format(url, get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))

    def get_obj_structure_url(self, url):
        return '{}?{}'.format(url, get_cms_setting('TOOLBAR_URL__BUILD'))

    def get_toolbar_disable_url(self, url):
        return '{}?{}'.format(url, get_cms_setting('TOOLBAR_URL__DISABLE'))


class CMSTestCase(BaseCMSTestCase, testcases.TestCase):

    def assertPending(self, page):
        if page.publisher_is_draft:
            # draft
            self.assertFalse(page.is_published('en'))
            self.assertTrue(bool(page.publisher_public_id))
            self.assertTrue(page.get_title_obj('en').published)
            self.assertEqual(page.get_publisher_state("en"), PUBLISHER_STATE_PENDING)
            self.assertPending(page.publisher_public)
        else:
            # public
            self.assertFalse(page.is_published('en'))
            self.assertTrue(bool(page.publisher_public_id))
            self.assertFalse(page.get_title_obj('en').published)

    def assertPublished(self, page):
        if page.publisher_is_draft:
            # draft
            self.assertTrue(page.is_published('en'))
            self.assertTrue(page.get_title_obj('en').published)
            self.assertTrue(bool(page.publisher_public_id))
            self.assertEqual(page.get_publisher_state("en"), PUBLISHER_STATE_DEFAULT)
            self.assertPublished(page.publisher_public)
        else:
            # public
            self.assertTrue(page.is_published('en'))
            self.assertTrue(page.get_title_obj('en').published)
            self.assertTrue(bool(page.publisher_public_id))

    def assertUnpublished(self, page):
        if page.publisher_is_draft:
            # draft
            self.assertFalse(page.is_published('en'))
            self.assertTrue(bool(page.publisher_public_id))
            self.assertFalse(page.get_title_obj('en').published)
            self.assertEqual(page.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)
            self.assertUnpublished(page.publisher_public)
        else:
            # public
            self.assertFalse(page.is_published('en'))
            self.assertTrue(bool(page.publisher_public_id))
            self.assertFalse(page.get_title_obj('en').published)

    def assertNeverPublished(self, page):
        self.assertTrue(page.publisher_is_draft)
        self.assertFalse(page.is_published('en'))
        self.assertIsNone(page.publisher_public)
        self.assertEqual(page.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)


class TransactionCMSTestCase(CMSTestCase, testcases.TransactionTestCase):
    pass
