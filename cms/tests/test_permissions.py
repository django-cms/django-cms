from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.db import OperationalError, ProgrammingError
from django.test.utils import override_settings

from cms.admin.permissionadmin import GlobalPagePermissionAdmin, PagePermissionInlineAdmin
from cms.api import add_plugin, assign_user_to_page, create_page
from cms.cache.permissions import (
    clear_user_permission_cache,
    get_permission_cache,
    set_permission_cache,
)
from cms.models import Page
from cms.models.permissionmodels import (
    ACCESS_CHILDREN,
    ACCESS_DESCENDANTS,
    ACCESS_PAGE,
    ACCESS_PAGE_AND_CHILDREN,
    ACCESS_PAGE_AND_DESCENDANTS,
    GlobalPagePermission,
    PagePermission,
    PermissionTuple,
)
from cms.test_utils.testcases import CMSTestCase
from cms.utils.compat.warnings import RemovedInDjangoCMS51Warning
from cms.utils.page_permissions import (
    get_change_perm_tuples,
    has_generic_permission,
    user_can_change_at_least_one_page,
    user_can_change_page_advanced_settings,
    user_can_delete_page,
    user_can_move_page,
    user_can_publish_page,
)


@override_settings(
    CMS_PERMISSION=True,
    CMS_CACHE_DURATIONS={
        'menus': 60,
        'content': 60,
        'permissions': 60,
    },
)
class PermissionCacheTests(CMSTestCase):

    def setUp(self):
        self.user_super = self._create_user("super", is_staff=True,
                                            is_superuser=True)
        self.user_normal = self._create_user("randomuser", is_staff=True,
                                             add_default_permissions=True)
        self.home_page = create_page("home", "nav_playground.html", "en",
                                     created_by=self.user_super)

    def test_basic_permissions(self):
        """
        Test basic permissions cache get / set / clear low-level api
        """
        cached_permissions = get_permission_cache(self.user_normal, "change_page")
        self.assertIsNone(cached_permissions)

        set_permission_cache(self.user_normal, "change_page", [self.home_page.id])
        cached_permissions = get_permission_cache(self.user_normal, "change_page")
        self.assertEqual(cached_permissions, [self.home_page.id])

        clear_user_permission_cache(self.user_normal)
        cached_permissions = get_permission_cache(self.user_normal, "change_page")
        self.assertIsNone(cached_permissions)

    def test_permission_manager(self):
        """
        Test page permission manager working on a subpage
        """
        page_b = create_page("page_b", "nav_playground.html", "en",
                             created_by=self.user_super)
        assign_user_to_page(page_b, self.user_normal, can_view=True,
                            can_change=True)
        cached_permissions = get_permission_cache(self.user_normal, "change_page")
        self.assertIsNone(cached_permissions)

        live_permissions = get_change_perm_tuples(self.user_normal, Site.objects.get_current())
        cached_permissions_permissions = get_permission_cache(self.user_normal,
                                                              "change_page")
        self.assertEqual(live_permissions, [(ACCESS_PAGE_AND_DESCENDANTS, page_b.node.path)])
        self.assertEqual(cached_permissions_permissions, live_permissions)

    def test_cached_permission_precedence(self):
        # refs - https://github.com/divio/django-cms/issues/6335
        # cached page permissions should not override global permissions
        page = create_page(
            "test page",
            "nav_playground.html",
            "en",
            created_by=self.user_super,
        )
        page_permission = GlobalPagePermission.objects.create(
            can_change=True,
            can_publish=True,
            user=self.user_normal,
        )
        page_permission.sites.add(Site.objects.get_current())
        set_permission_cache(self.user_normal, "publish_page", [])

        can_publish = user_can_publish_page(
            self.user_normal,
            page,
            Site.objects.get_current(),
        )
        self.assertTrue(can_publish)

    def test_has_generic_permissions_compatibiltiy(self):
        from cms.utils.permissions import has_page_permission

        page_b = create_page("page_b", "nav_playground.html", "en",
                             created_by=self.user_super)
        assign_user_to_page(page_b, self.user_normal, can_view=True,
                            can_change=True)

        self.assertTrue(has_generic_permission(page_b, self.user_normal, "change_page"))
        self.assertFalse(has_generic_permission(page_b, self.user_normal, "publish_page"))

        message = ("has_page_permission is deprecated. "
                   "Use cms.utils.page_permissions.has_generic_permission instead.")
        # Backwards compatibility: check if the old permission names work
        with self.assertWarns(RemovedInDjangoCMS51Warning) as w:
            self.assertTrue(has_page_permission(self.user_normal, page_b, "change"))
        self.assertEqual(str(w.warning), message)
        with self.assertWarns(RemovedInDjangoCMS51Warning) as w:
            self.assertFalse(has_page_permission(self.user_normal, page_b, "publish"))
        self.assertEqual(str(w.warning), message)

@override_settings(CMS_PERMISSION=True, CMS_RAW_ID_USERS=1)
class PermissionAdminMigrationSafetyTests(CMSTestCase):
    """
    Regression tests for the case where the user table does not yet exist
    (e.g. during ``migrate`` on a fresh install with a custom user model).

    Counting users then raises ``OperationalError`` on sqlite or
    ``ProgrammingError`` on postgres. Both must be swallowed so that the
    admin classes can still be imported and registered during migrations.
    """

    def _patched_user_model(self, exc):
        class _BrokenManager:
            def count(self):
                raise exc

        class _BrokenUserModel:
            objects = _BrokenManager()

        return patch(
            'cms.admin.permissionadmin.get_user_model',
            return_value=_BrokenUserModel,
        )

    def test_inline_raw_id_fields_swallows_db_errors(self):
        for exc in (OperationalError("no such table"), ProgrammingError("relation does not exist")):
            with self.subTest(exc=type(exc).__name__), self._patched_user_model(exc):
                self.assertEqual(PagePermissionInlineAdmin.raw_id_fields, [])

    def test_global_admin_raw_id_fields_swallows_db_errors(self):
        for exc in (OperationalError("no such table"), ProgrammingError("relation does not exist")):
            with self.subTest(exc=type(exc).__name__), self._patched_user_model(exc):
                self.assertEqual(GlobalPagePermissionAdmin.raw_id_fields, [])

    def test_global_admin_get_list_filter_swallows_db_errors(self):
        admin_instance = GlobalPagePermissionAdmin(GlobalPagePermission, admin_site=None)
        for exc in (OperationalError("no such table"), ProgrammingError("relation does not exist")):
            with self.subTest(exc=type(exc).__name__), self._patched_user_model(exc):
                # Falls back to the unfiltered list_filter (still includes 'user')
                self.assertIn('user', admin_instance.get_list_filter(request=None))


class PermissionTupleTests(CMSTestCase):
    """
    Regression tests for ``PermissionTuple.allow_list()`` building invalid
    lookups (``page____path__length``) for ACCESS_CHILDREN,
    ACCESS_DESCENDANTS and ACCESS_PAGE_AND_CHILDREN (#8661).
    """

    def setUp(self):
        self.root = create_page("root", "nav_playground.html", "en")
        self.child = create_page("child", "nav_playground.html", "en", parent=self.root)
        self.grandchild = create_page("grandchild", "nav_playground.html", "en", parent=self.child)
        self.sibling = create_page("sibling", "nav_playground.html", "en")

    def test_allow_list_scopes(self):
        cases = (
            (ACCESS_PAGE, {self.root}),
            (ACCESS_CHILDREN, {self.child}),
            (ACCESS_PAGE_AND_CHILDREN, {self.root, self.child}),
            (ACCESS_DESCENDANTS, {self.child, self.grandchild}),
            (ACCESS_PAGE_AND_DESCENDANTS, {self.root, self.child, self.grandchild}),
        )
        for grant_on, expected in cases:
            with self.subTest(grant_on=grant_on):
                perm = PermissionTuple((grant_on, self.root.path))
                allowed = Page.objects.filter(perm.allow_list())
                self.assertEqual(set(allowed), expected)

    def test_allow_list_matches_contains(self):
        pages = list(Page.objects.all())
        grants = (ACCESS_PAGE, ACCESS_CHILDREN, ACCESS_PAGE_AND_CHILDREN,
                  ACCESS_DESCENDANTS, ACCESS_PAGE_AND_DESCENDANTS)
        for grant_on in grants:
            with self.subTest(grant_on=grant_on):
                perm = PermissionTuple((grant_on, self.root.path))
                expected = {page.pk for page in pages if perm.contains(page.path)}
                allowed = Page.objects.filter(perm.allow_list()).values_list("pk", flat=True)
                self.assertEqual(set(allowed), expected)

    def test_allow_list_with_related_field_prefix(self):
        user = self._create_user("perm-user", is_staff=True)
        for page in (self.root, self.child, self.grandchild, self.sibling):
            PagePermission.objects.create(page=page, user=user, grant_on=ACCESS_PAGE)
        perm = PermissionTuple((ACCESS_PAGE_AND_CHILDREN, self.root.path))
        matched = PagePermission.objects.filter(perm.allow_list("page"))
        self.assertEqual({pp.page_id for pp in matched}, {self.root.pk, self.child.pk})


@override_settings(CMS_PERMISSION=True)
class DeletePagePlaceholderPermissionTests(CMSTestCase):
    """
    ``user_can_delete_page`` must evaluate the delete permission of the
    plugins in each of the page's placeholders.

    Regression tests for issue 03: the placeholder loop accessed ``.source``
    on the queryset instead of the loop variable (``AttributeError``), and
    the placeholder lookup filtered on the ``Placeholder`` content type
    instead of ``PageContent``, so the loop never ran at all.
    """

    def _get_page_with_plugin(self):
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot="body")
        add_plugin(
            placeholder,
            "LinkPlugin",
            "en",
            name="A link",
            external_link="https://www.django-cms.org",
        )
        return page

    def test_user_with_plugin_permissions_can_delete_page(self):
        page = self._get_page_with_plugin()
        # add_default_permissions grants add/change/delete on the Link plugin model
        user = self._create_user(
            "page-deleter",
            is_staff=True,
            add_default_permissions=True,
            permissions=["change_page", "delete_page"],
        )
        self.add_global_permission(user, can_change=True, can_delete=True)

        self.assertTrue(user_can_delete_page(user, page))

    def test_user_without_plugin_permissions_cannot_delete_page(self):
        page = self._get_page_with_plugin()
        # No plugin model permissions: deleting the page would delete the
        # Link plugin in its placeholder, which this user may not do.
        user = self._create_user(
            "page-deleter-no-plugin-perms",
            is_staff=True,
            permissions=["change_page", "delete_page"],
        )
        self.add_global_permission(user, can_change=True, can_delete=True)

        self.assertFalse(user_can_delete_page(user, page))


@override_settings(
    CMS_PERMISSION=True,
    CMS_CACHE_DURATIONS={
        'menus': 60,
        'content': 60,
        'permissions': 60,
    },
)
class PermissionCacheInvalidationTests(CMSTestCase):
    """
    Saving or deleting users and changing their group memberships must
    invalidate the permission cache.

    Regression tests for issue 10: the signal handlers were connected to the
    hardcoded ``django.contrib.auth.models.User``, so projects with a custom
    ``AUTH_USER_MODEL`` got no cache invalidation. These tests exercise the
    handlers through the model returned by ``get_user_model()`` and fail in
    test runs with a custom user model (``--auth-user-model``) if the
    binding regresses.
    """

    def setUp(self):
        self.user_super = self._create_user("super", is_staff=True, is_superuser=True)
        self.user_normal = self._create_user("randomuser", is_staff=True, add_default_permissions=True)
        self.home_page = create_page("home", "nav_playground.html", "en", created_by=self.user_super)

    def _fill_permission_cache(self):
        set_permission_cache(self.user_normal, Site.objects.get_current(), "change_page", [self.home_page.id])
        self.assertIsNotNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))

    def test_user_save_clears_permission_cache(self):
        self._fill_permission_cache()
        self.user_normal.save()
        self.assertIsNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))

    def test_user_delete_clears_permission_cache(self):
        self._fill_permission_cache()
        self.user_normal.delete()
        self.assertIsNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))

    def test_group_membership_change_clears_permission_cache(self):
        group = Group.objects.create(name="permission-cache-group")
        self._fill_permission_cache()
        self.user_normal.groups.add(group)
        self.assertIsNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))

    def test_group_delete_clears_permission_cache_of_members(self):
        group = Group.objects.create(name="permission-cache-group")
        self.user_normal.groups.add(group)
        self._fill_permission_cache()
        group.delete()
        self.assertIsNone(get_permission_cache(self.user_normal, Site.objects.get_current(), "change_page"))


@override_settings(
    CMS_PERMISSION=True,
    CMS_CACHE_DURATIONS={
        'menus': 60,
        'content': 60,
        'permissions': 60,
    },
    CMS_LANGUAGES={
        1: [{'code': 'en', 'name': 'English'}],
        2: [{'code': 'en', 'name': 'English'}],
    },
)
class PermissionCacheSiteIsolationTests(CMSTestCase):
    """The cached page permissions of one site must not be served for another.

    ``get_page_actions_for_user`` filters by site, so a value warmed while
    browsing a site the user works on used to satisfy the "can change at least
    one page" gate of every other site, disclosing their page trees.
    """

    def setUp(self):
        super().setUp()
        cache.clear()
        self.site_a = Site.objects.get_current()
        self.site_b = Site.objects.create(domain='b.example', name='B')
        self.user = self._create_user('editor', is_staff=True, add_default_permissions=True)
        self.page_a = create_page('site-a', 'nav_playground.html', 'en', site=self.site_a)
        assign_user_to_page(self.page_a, self.user, can_view=True, can_change=True)
        self.secret_b = create_page('SECRET-SITE-B', 'nav_playground.html', 'en', site=self.site_b)

    def get_tree(self, site):
        return self.client.get(self.get_admin_url(PageContent, 'get_tree') + f'?site={site.pk}')

    def test_cache_key_includes_the_site(self):
        self.assertNotEqual(
            get_cache_key(self.user, self.site_a, 'change_page'),
            get_cache_key(self.user, self.site_b, 'change_page'),
        )

    def test_cached_permissions_are_not_reused_across_sites(self):
        self.assertTrue(user_can_change_at_least_one_page(self.user, self.site_a))
        self.assertIsNotNone(get_permission_cache(self.user, self.site_a, 'change_page'))
        self.assertIsNone(get_permission_cache(self.user, self.site_b, 'change_page'))
        self.assertFalse(user_can_change_at_least_one_page(self.user, self.site_b))

    def test_warming_one_site_does_not_disclose_another(self):
        with self.login_user_context(self.user):
            self.assertEqual(self.get_tree(self.site_a).status_code, 200)
            # The gate of site B must not be satisfied by the value just warmed.
            response = self.get_tree(self.site_b)
        self.assertEqual(response.status_code, 403)

    def test_own_site_stays_reachable_when_cache_is_warm(self):
        with self.login_user_context(self.user):
            self.get_tree(self.site_b)
            response = self.get_tree(self.site_a)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'site-a')

    def test_clear_user_permission_cache_clears_every_site(self):
        set_permission_cache(self.user, self.site_a, 'change_page', [self.page_a.path])
        set_permission_cache(self.user, self.site_b, 'change_page', [self.secret_b.path])

        clear_user_permission_cache(self.user)

        self.assertIsNone(get_permission_cache(self.user, self.site_a, 'change_page'))
        self.assertIsNone(get_permission_cache(self.user, self.site_b, 'change_page'))


@override_settings(CMS_PERMISSION=True)
class DeprecatedSiteAccessHelperTests(CMSTestCase):
    """``user_can_access_site``/``raise_site_permission_denied`` are unused.

    Site isolation is enforced by ``PageContentAdmin.has_change_permission()``.
    """

    def get_admin(self):
        return admin.site._registry[PageContent]

    def test_user_can_access_site_warns(self):
        request = self.get_request("/en/")
        request.user = self.get_superuser()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RemovedInDjangoCMS60Warning)
            self.assertTrue(self.get_admin().user_can_access_site(request))

        self.assertTrue(
            any(issubclass(warning.category, RemovedInDjangoCMS60Warning) for warning in caught),
            "Expected a deprecation warning from user_can_access_site().",
        )

    def test_raise_site_permission_denied_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RemovedInDjangoCMS60Warning)
            with self.assertRaises(PermissionDenied):
                self.get_admin().raise_site_permission_denied()

        self.assertTrue(
            any(issubclass(warning.category, RemovedInDjangoCMS60Warning) for warning in caught),
            "Expected a deprecation warning from raise_site_permission_denied().",
        )


@override_settings(CMS_PERMISSION=True)
class GlobalPagePermissionEscalationTests(CMSTestCase):
    """A permission manager must not grant rights they do not hold themselves.

    ``GlobalPagePermissionAdmin`` used to expose every ``can_*`` flag
    unconditionally, so a delegate holding only ``can_change_permissions`` could
    POST themselves ``can_publish``/``can_delete``/``can_change_advanced_settings``/
    ``can_move_page`` site-wide (CWE-269).
    """

    add_url = '/en/admin/cms/globalpagepermission/add/'

    def _create_delegate(self, username='delegate', sites=None, **flags):
        user = self._create_user(username, is_staff=True, is_superuser=False)
        for codename in ('add_globalpagepermission', 'change_globalpagepermission'):
            user.user_permissions.add(Permission.objects.get(codename=codename))
        # The page model permissions a delegated manager normally carries; the
        # CMS grant below is what actually limits them.
        user.user_permissions.add(
            *Permission.objects.filter(codename__in=[
                'change_page', 'publish_page', 'change_page_advanced_settings',
                'move_page', 'delete_page',
            ])
        )
        defaults = dict.fromkeys(GlobalPagePermission.get_all_permissions(), False)
        defaults.update(can_change=True, can_change_permissions=True, **flags)
        grant = GlobalPagePermission.objects.create(user=user, **defaults)
        grant.sites.set(sites if sites is not None else [Site.objects.get_current()])
        return self.reload(user), grant

    def _post(self, actor, **extra):
        data = {
            'user': actor.pk,
            'group': '',
            'sites': [Site.objects.get_current().pk],
            '_save': 'Save',
        }
        data.update(extra)
        with self.login_user_context(actor):
            return self.client.post(self.add_url, data)

    def test_delegate_cannot_grant_flags_it_does_not_hold(self):
        page = create_page('secret', 'nav_playground.html', 'en')
        delegate, _grant = self._create_delegate()

        self.assertFalse(user_can_publish_page.without_cache(delegate, page))

        response = self._post(
            delegate,
            can_add='on', can_change='on', can_delete='on', can_publish='on',
            can_change_advanced_settings='on', can_change_permissions='on',
            can_move_page='on', can_view='on',
        )
        self.assertEqual(response.status_code, 302)

        # A row is still created -- the manager may delegate what they hold --
        # but only with the flags they actually have.
        escalated = GlobalPagePermission.objects.filter(user=delegate).exclude(pk=_grant.pk)
        self.assertEqual(escalated.count(), 1)
        new_grant = escalated.get()
        for flag in ('can_add', 'can_delete', 'can_publish',
                     'can_change_advanced_settings', 'can_move_page', 'can_view'):
            self.assertFalse(getattr(new_grant, flag), f'{flag} was granted')
        # The two rights the delegate does hold are theirs to delegate.
        self.assertTrue(new_grant.can_change)
        self.assertTrue(new_grant.can_change_permissions)

        clear_user_permission_cache(delegate)
        delegate = self.reload(delegate)
        self.assertFalse(user_can_publish_page.without_cache(delegate, page))
        self.assertFalse(user_can_change_page_advanced_settings.without_cache(delegate, page))
        self.assertFalse(user_can_move_page.without_cache(delegate, page))

    def test_delegate_can_grant_flags_it_holds(self):
        delegate, _grant = self._create_delegate(can_publish=True)
        target = self._create_user('target', is_staff=True)

        response = self._post(delegate, user=target.pk, can_change='on', can_publish='on')
        self.assertEqual(response.status_code, 302)

        new_grant = GlobalPagePermission.objects.get(user=target)
        self.assertTrue(new_grant.can_change)
        self.assertTrue(new_grant.can_publish)

    def test_flag_held_on_one_site_cannot_be_granted_on_another(self):
        other_site = Site.objects.create(domain='other.example.com', name='other')
        delegate, _grant = self._create_delegate(can_publish=True)
        # Permission management on both sites, publishing on the current one only.
        other_grant = self._create_grant(delegate, sites=[other_site], can_change_permissions=True)
        delegate = self.reload(delegate)

        response = self._post(
            delegate,
            sites=[Site.objects.get_current().pk, other_site.pk],
            can_change='on', can_publish='on',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('can_publish', response.context_data['adminform'].form.errors)
        self.assertFalse(
            GlobalPagePermission.objects.filter(user=delegate)
            .exclude(pk__in=[_grant.pk, other_grant.pk]).exists()
        )

    def test_all_sites_grant_requires_unrestricted_rights(self):
        """An empty ``sites`` means every site, so a site-scoped manager cannot use it."""
        delegate, _grant = self._create_delegate(can_publish=True)

        response = self._post(delegate, sites=[], can_change='on', can_publish='on')
        self.assertEqual(response.status_code, 200)
        self.assertIn('sites', response.context_data['adminform'].form.errors)

    def _change_url(self, grant):
        return f'/en/admin/cms/globalpagepermission/{grant.pk}/change/'

    def _create_grant(self, user, sites=None, **flags):
        defaults = dict.fromkeys(GlobalPagePermission.get_all_permissions(), False)
        defaults.update(can_change=True, **flags)
        grant = GlobalPagePermission.objects.create(user=user, **defaults)
        grant.sites.set(sites if sites is not None else [Site.objects.get_current()])
        return grant

    def test_grant_with_untouchable_flags_cannot_be_changed(self):
        """Flags the manager may not grant are also flags they may not strip."""
        delegate, _grant = self._create_delegate()
        target = self._create_user('target', is_staff=True)
        existing = self._create_grant(
            target, can_publish=True, can_delete=True, can_change_advanced_settings=True,
        )

        with self.login_user_context(delegate):
            response = self.client.post(self._change_url(existing), {
                'user': target.pk,
                'group': '',
                'sites': [Site.objects.get_current().pk],
                'can_change': 'on',
                '_save': 'Save',
            })
        self.assertEqual(response.status_code, 403)

        existing.refresh_from_db()
        self.assertTrue(existing.can_publish)
        self.assertTrue(existing.can_delete)
        self.assertTrue(existing.can_change_advanced_settings)

    def test_grant_with_untouchable_flags_cannot_be_reassigned(self):
        """Changing ``user`` must not move a flag the manager does not hold to themselves."""
        page = create_page('secret', 'nav_playground.html', 'en')
        delegate, _grant = self._create_delegate()
        target = self._create_user('target', is_staff=True)
        existing = self._create_grant(target, can_publish=True)

        with self.login_user_context(delegate):
            response = self.client.post(self._change_url(existing), {
                'user': delegate.pk,
                'group': '',
                'sites': [Site.objects.get_current().pk],
                'can_change': 'on',
                'can_change_permissions': 'on',
                '_save': 'Save',
            })
        self.assertEqual(response.status_code, 403)

        existing.refresh_from_db()
        self.assertEqual(existing.user, target)
        clear_user_permission_cache(delegate)
        self.assertFalse(user_can_publish_page.without_cache(self.reload(delegate), page))

    def test_grant_on_other_site_cannot_be_changed(self):
        """A flag held on one site does not reach a grant for another site."""
        other_site = Site.objects.create(domain='other.example.com', name='other')
        delegate, _grant = self._create_delegate(can_publish=True)
        target = self._create_user('target', is_staff=True)
        existing = self._create_grant(target, sites=[other_site], can_publish=True)

        with self.login_user_context(delegate):
            response = self.client.get(self._change_url(existing))
        self.assertFalse(response.context_data['has_change_permission'])

    def test_grant_with_untouchable_flags_cannot_be_deleted(self):
        delegate, _grant = self._create_delegate()
        delegate.user_permissions.add(Permission.objects.get(codename='delete_globalpagepermission'))
        delegate = self.reload(delegate)
        target = self._create_user('target', is_staff=True)
        existing = self._create_grant(target, can_publish=True)

        with self.login_user_context(delegate):
            response = self.client.post(
                f'/en/admin/cms/globalpagepermission/{existing.pk}/delete/', {'post': 'yes'},
            )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(GlobalPagePermission.objects.filter(pk=existing.pk).exists())

    def test_grant_within_managers_rights_can_be_changed(self):
        delegate, _grant = self._create_delegate(can_publish=True)
        target = self._create_user('target', is_staff=True)
        existing = self._create_grant(target, can_publish=True)

        with self.login_user_context(delegate):
            response = self.client.post(self._change_url(existing), {
                'user': target.pk,
                'group': '',
                'sites': [Site.objects.get_current().pk],
                'can_change': 'on',
                '_save': 'Save',
            })
        self.assertEqual(response.status_code, 302)

        existing.refresh_from_db()
        self.assertTrue(existing.can_change)
        self.assertFalse(existing.can_publish)

    def test_flag_without_django_permission_cannot_be_granted(self):
        """A CMS flag is no right without the Django permission page actions require."""
        page = create_page('secret', 'nav_playground.html', 'en')
        delegate, _grant = self._create_delegate(can_publish=True)
        delegate.user_permissions.remove(Permission.objects.get(codename='publish_page'))
        delegate = self.reload(delegate)
        self.assertFalse(user_can_publish_page.without_cache(delegate, page))

        target = self._create_user('target', is_staff=True)
        target.user_permissions.add(
            *Permission.objects.filter(codename__in=['change_page', 'publish_page'])
        )
        response = self._post(delegate, user=target.pk, can_change='on', can_publish='on')
        self.assertEqual(response.status_code, 302)

        new_grant = GlobalPagePermission.objects.get(user=target)
        self.assertTrue(new_grant.can_change)
        self.assertFalse(new_grant.can_publish)
        self.assertFalse(user_can_publish_page.without_cache(self.reload(target), page))

    def _create_manager_of_other_site(self):
        """A delegate managing permissions on the current site only, but publishing on another."""
        other_site = Site.objects.create(domain='other.example.com', name='other')
        delegate, _grant = self._create_delegate()
        self._create_grant(delegate, sites=[other_site], can_publish=True)
        return self.reload(delegate), other_site

    def test_grant_requires_permission_management_on_every_selected_site(self):
        delegate, other_site = self._create_manager_of_other_site()
        target = self._create_user('target', is_staff=True)

        response = self._post(
            delegate, user=target.pk, sites=[other_site.pk], can_change='on', can_publish='on',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('sites', response.context_data['adminform'].form.errors)
        self.assertFalse(GlobalPagePermission.objects.filter(user=target).exists())

    def test_grant_on_site_without_permission_management_cannot_be_changed(self):
        delegate, other_site = self._create_manager_of_other_site()
        target = self._create_user('target', is_staff=True)
        existing = self._create_grant(target, sites=[other_site], can_publish=True)

        with self.login_user_context(delegate):
            response = self.client.post(self._change_url(existing), {
                'user': delegate.pk,
                'group': '',
                'sites': [other_site.pk],
                'can_change': 'on',
                'can_publish': 'on',
                '_save': 'Save',
            })
        self.assertEqual(response.status_code, 403)
        existing.refresh_from_db()
        self.assertEqual(existing.user, target)

    def test_superuser_is_unrestricted(self):
        superuser = self.get_superuser()
        target = self._create_user('target', is_staff=True)

        response = self._post(
            superuser, user=target.pk,
            can_change='on', can_publish='on', can_delete='on',
            can_change_advanced_settings='on', can_move_page='on',
        )
        self.assertEqual(response.status_code, 302)

        new_grant = GlobalPagePermission.objects.get(user=target)
        self.assertTrue(new_grant.can_publish)
        self.assertTrue(new_grant.can_change_advanced_settings)
        self.assertTrue(new_grant.can_move_page)
