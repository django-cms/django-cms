from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.sites.models import Site
from django.db.models import Q
from django.test.client import RequestFactory
from django.test.utils import override_settings

from cms.admin.forms import save_permissions
from cms.api import assign_user_to_page, create_page, create_page_user
from cms.cms_menus import get_visible_nodes
from cms.models import ACCESS_PAGE, Page, PageContent
from cms.models.permissionmodels import (
    ACCESS_PAGE_AND_DESCENDANTS,
    GlobalPagePermission,
    PagePermission,
)
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.utils import get_current_site
from cms.utils.page_permissions import user_can_view_page


@override_settings(CMS_PERMISSION=True)
class PermissionModeratorTests(CMSTestCase):
    """Permissions and moderator together

    Fixtures contains 3 users and 1 published page and some other stuff

    Users:
        1. `super`: superuser
        2. `master`: user with permissions to all applications
        3. `slave`: user assigned to page `slave-home`

    Pages:
        1. `home`:
            - published page
            - master can do anything on its subpages, but not on home!

        2. `master`:
            - published page
            - created by super
            - `master` can do anything on it and its descendants
            - subpages:

        3.       `slave-home`:
                    - not published
                    - assigned slave user which can add/change/delete/
                      move/publish this page and its descendants
                    - `master` user want to moderate this page and all descendants

        4. `pageA`:
            - created by super
            - master can add/change/delete on it and descendants
    """
    # TODO: Split this test case into one that tests publish functionality, and
    # TODO: one that tests permission inheritance. This is too complex.

    def setUp(self):
        # create super user
        self.user_super = self._create_user("super", is_staff=True,
                                            is_superuser=True)
        self.user_staff = self._create_user("staff", is_staff=True,
                                            add_default_permissions=True)
        self.user_master = self._create_user("master", is_staff=True,
                                             add_default_permissions=True)
        self.user_slave = self._create_user("slave", is_staff=True,
                                            add_default_permissions=True)
        self.user_normal = self._create_user("normal", is_staff=False)

        with self.login_user_context(self.user_super):
            self.home_page = create_page("home", "nav_playground.html", "en",
                                         created_by=self.user_super)

            # master page & master user
            self.master_page = create_page("master", "nav_playground.html", "en")

            # create non global, non staff user
            self.user_non_global = self._create_user("nonglobal")

            # assign master user under home page
            assign_user_to_page(self.home_page, self.user_master,
                                grant_on=ACCESS_PAGE_AND_DESCENDANTS, grant_all=True)

            # and to master page
            assign_user_to_page(self.master_page, self.user_master,
                                grant_on=ACCESS_PAGE_AND_DESCENDANTS, grant_all=True)

            # slave page & slave user

            self.slave_page = create_page("slave-home", "col_two.html", "en",
                                          parent=self.master_page, created_by=self.user_super)

            assign_user_to_page(self.slave_page, self.user_slave, grant_all=True)

            # create page_b
            self.page_b = create_page("pageB", "nav_playground.html", "en", created_by=self.user_super)
            # Normal user

            # it's allowed for the normal user to view the page
            assign_user_to_page(self.page_b, self.user_normal, can_view=True)

            # create page_a - sample page from master

            page_a = create_page("pageA", "nav_playground.html", "en",
                                 created_by=self.user_super)
            assign_user_to_page(page_a, self.user_master,
                                can_add=True, can_change=True, can_delete=True,
                                can_move_page=True)

    def _add_plugin(self, user, page):
        """
        Add a plugin using the test client to check for permissions.
        """
        with self.login_user_context(user):
            placeholder = page.get_placeholders('en')[0]
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
            endpoint = self.get_add_plugin_uri(
                placeholder=placeholder,
                plugin_type='LinkPlugin',
                language='en',
            )
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            return response.content.decode('utf8')

    def test_super_can_add_page_to_root(self):
        with self.login_user_context(self.user_super):
            response = self.client.get(self.get_page_add_uri('en'))
            self.assertEqual(response.status_code, 200)

    def test_master_cannot_add_page_to_root(self):
        with self.login_user_context(self.user_master):
            response = self.client.get(self.get_page_add_uri('en'))
            self.assertEqual(response.status_code, 403)

    def test_slave_cannot_add_page_to_root(self):
        with self.login_user_context(self.user_slave):
            response = self.client.get(self.get_page_add_uri('en'))
            self.assertEqual(response.status_code, 403)

    def test_super_can_add_plugin(self):
        self._add_plugin(self.user_super, page=self.slave_page)

    def test_master_can_add_plugin(self):
        self._add_plugin(self.user_master, page=self.slave_page)

    def test_slave_can_add_plugin(self):
        self._add_plugin(self.user_slave, page=self.slave_page)

    def test_superuser_can_view(self):
        url = self.page_b.get_absolute_url(language='en')
        with self.login_user_context(self.user_super):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_staff_can_view(self):
        url = self.page_b.get_absolute_url(language='en')
        all_view_perms = PagePermission.objects.filter(can_view=True)
        # verify that the user_staff has access to this page
        has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b:
                if perm.user == self.user_staff:
                    has_perm = True
        self.assertEqual(has_perm, False)
        login_ok = self.client.login(username=getattr(self.user_staff, get_user_model().USERNAME_FIELD),
                                     password=getattr(self.user_staff, get_user_model().USERNAME_FIELD))
        self.assertTrue(login_ok)

        # really logged in
        self.assertTrue('_auth_user_id' in self.client.session)
        login_user_id = self.client.session.get('_auth_user_id')
        user = get_user_model().objects.get(pk=self.user_staff.pk)
        self.assertEqual(str(login_user_id), str(user.id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_normal_can_view(self):
        url = self.page_b.get_absolute_url(language='en')
        all_view_perms = PagePermission.objects.filter(can_view=True)
        # verify that the normal_user has access to this page
        normal_has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b:
                if perm.user == self.user_normal:
                    normal_has_perm = True
        self.assertTrue(normal_has_perm)
        with self.login_user_context(self.user_normal):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        # verify that the user_non_global has not access to this page
        non_global_has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b:
                if perm.user == self.user_non_global:
                    non_global_has_perm = True
        self.assertFalse(non_global_has_perm)
        with self.login_user_context(self.user_non_global):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

        # non logged in user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_globalpermission(self):
        # Global user
        user_global = self._create_user("global")

        with self.login_user_context(self.user_super):
            user_global = create_page_user(user_global, user_global)
            user_global.is_staff = False
            user_global.save()  # Prevent is_staff permission
            global_page = create_page("global", "nav_playground.html", "en")
            assign_user_to_page(global_page, user_global, global_permission=True, can_view=True)

        url = global_page.get_absolute_url('en')
        all_view_perms = PagePermission.objects.filter(can_view=True)
        has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b and perm.user == user_global:
                has_perm = True
        self.assertEqual(has_perm, False)

        global_page_perm_q = Q(user=user_global) & Q(can_view=True)
        global_view_perms = GlobalPagePermission.objects.filter(global_page_perm_q).exists()
        self.assertEqual(global_view_perms, True)

        # user_global
        with self.login_user_context(user_global):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            # self.non_user_global
        has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b and perm.user == self.user_non_global:
                has_perm = True
        self.assertEqual(has_perm, False)

        global_page_perm_q = Q(user=self.user_non_global) & Q(can_view=True)
        global_view_perms = GlobalPagePermission.objects.filter(global_page_perm_q).exists()
        self.assertEqual(global_view_perms, False)

        with self.login_user_context(self.user_non_global):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

    def test_anonymous_user_public_for_all(self):
        url = self.page_b.get_absolute_url('en')
        with self.settings(CMS_PUBLIC_FOR='all'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

    def test_anonymous_user_public_for_none(self):
        # default of when to show pages to anonymous user doesn't take
        # global permissions into account
        url = self.page_b.get_absolute_url('en')
        with self.settings(CMS_PUBLIC_FOR=None):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)


class ViewPermissionBaseTests(CMSTestCase):

    def setUp(self):
        self.page = create_page('testpage', 'nav_playground.html', 'en')
        self.site = get_current_site()

    def get_request(self, user=None):
        attrs = {
            'user': user or AnonymousUser(),
            'REQUEST': {},
            'POST': {},
            'GET': {},
            'session': {},
        }
        return type('Request', (object,), attrs)

    def assertViewAllowed(self, page, user=None):
        if not user:
            user = AnonymousUser()
        self.assertTrue(user_can_view_page(user, page))

    def assertViewNotAllowed(self, page, user=None):
        if not user:
            user = AnonymousUser()
        self.assertFalse(user_can_view_page(user, page))


@override_settings(
    CMS_PERMISSION=False,
    CMS_PUBLIC_FOR='staff',
)
class BasicViewPermissionTests(ViewPermissionBaseTests):
    """
    Test functionality with CMS_PERMISSION set to false, as this is the
    normal use case
    """

    @override_settings(CMS_PUBLIC_FOR="all")
    def test_unauth_public(self):
        request = self.get_request()
        with self.assertNumQueries(0):
            self.assertViewAllowed(self.page)

        self.assertEqual(get_visible_nodes(request, [self.page], self.site),
                         [self.page])

    def test_unauth_non_access(self):
        request = self.get_request()
        with self.assertNumQueries(0):
            self.assertViewNotAllowed(self.page)

        self.assertEqual(get_visible_nodes(request, [self.page], self.site),
                         [])

    @override_settings(CMS_PUBLIC_FOR="all")
    def test_staff_public_all(self):
        user = self.get_staff_user_with_no_permissions()
        request = self.get_request(user)

        with self.assertNumQueries(0):
            self.assertViewAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, [self.page], self.site),
                         [self.page])

    def test_staff_public_staff(self):
        user = self.get_staff_user_with_no_permissions()
        request = self.get_request(user)

        with self.assertNumQueries(0):
            self.assertViewAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, [self.page], self.site),
                         [self.page])

    def test_staff_basic_auth(self):
        user = self.get_staff_user_with_no_permissions()
        request = self.get_request(user)

        with self.assertNumQueries(0):
            self.assertViewAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, [self.page], self.site),
                         [self.page])

    @override_settings(CMS_PUBLIC_FOR="all")
    def test_normal_basic_auth(self):
        user = self.get_standard_user()
        request = self.get_request(user)

        with self.assertNumQueries(0):
            self.assertViewAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, [self.page], self.site), [self.page])


@override_settings(
    CMS_PERMISSION=True,
    CMS_PUBLIC_FOR='none'
)
class UnrestrictedViewPermissionTests(ViewPermissionBaseTests):
    """
        Test functionality with CMS_PERMISSION set to True but no restrictions
        apply to this specific page
    """

    def test_unauth_non_access(self):
        request = self.get_request()

        with self.assertNumQueries(1):
            """
            The query is:
            PagePermission query for the affected page (is the page restricted?)
            """
            self.assertViewNotAllowed(self.page)

        self.assertEqual(get_visible_nodes(request, [self.page], self.site), [])

    def test_global_access(self):
        user = self.get_standard_user()
        GlobalPagePermission.objects.create(can_view=True, user=user)
        request = self.get_request(user)

        with self.assertNumQueries(4):
            """The queries are:
            PagePermission query for the affected page (is the page restricted?)
            Generic django permission lookup
            content type lookup by permission lookup
            GlobalPagePermission query for the page site
            """
            self.assertViewAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, [self.page], self.site), [self.page])

    def test_normal_denied(self):
        user = self.get_standard_user()
        request = self.get_request(user)

        with self.assertNumQueries(4):
            """
            The queries are:
            PagePermission query for the affected page (is the page restricted?)
            GlobalPagePermission query for the page site
            User permissions query
            Content type query
            """
            self.assertViewNotAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, [self.page], self.site), [])


@override_settings(
    CMS_PERMISSION=True,
    CMS_PUBLIC_FOR='all'
)
class RestrictedViewPermissionTests(ViewPermissionBaseTests):
    """
    Test functionality with CMS_PERMISSION set to True and view restrictions
    apply to this specific page
    """
    def setUp(self):
        super().setUp()
        self.group = Group.objects.create(name='testgroup')
        self.pages = [self.page]
        self.expected = [self.page]
        PagePermission.objects.create(page=self.page, group=self.group, can_view=True, grant_on=ACCESS_PAGE)

    def test_unauthed(self):
        request = self.get_request()
        with self.assertNumQueries(1):
            """The queries are:
            PagePermission query for the affected page (is the page restricted?)
            """
            self.assertViewNotAllowed(self.page)

        self.assertEqual(get_visible_nodes(request, self.pages, self.site), [])

    def test_page_permissions(self):
        user = self.get_standard_user()
        request = self.get_request(user)
        PagePermission.objects.create(can_view=True, user=user, page=self.page, grant_on=ACCESS_PAGE)

        with self.assertNumQueries(6):
            """
            The queries are:
            PagePermission query (is this page restricted)
            content type lookup (x2)
            GlobalpagePermission query for user
            TreeNode lookup
            PagePermission query for this user
            """
            self.assertViewAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, self.pages, self.site), self.expected)

    def test_page_group_permissions(self):
        user = self.get_standard_user()
        user.groups.add(self.group)
        request = self.get_request(user)

        with self.assertNumQueries(6):
            """
                The queries are:
                PagePermission query (is this page restricted)
                content type lookup (x2)
                GlobalpagePermission query for user
                TreeNode lookup
                PagePermission query for user
            """
            self.assertViewAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, self.pages, self.site), self.expected)

    def test_global_permission(self):
        user = self.get_standard_user()
        GlobalPagePermission.objects.create(can_view=True, user=user)
        request = self.get_request(user)

        with self.assertNumQueries(4):
            """
            The queries are:
            PagePermission query (is this page restricted)
            Generic django permission lookup
            content type lookup by permission lookup
            GlobalpagePermission query for user
            """
            self.assertViewAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, self.pages, self.site), self.expected)

    def test_basic_perm_denied(self):
        user = self.get_staff_user_with_no_permissions()
        request = self.get_request(user)

        with self.assertNumQueries(6):
            """
            The queries are:
            PagePermission query (is this page restricted)
            content type lookup x2
            GlobalpagePermission query for user
            TreeNode lookup
            PagePermission query for this user
            """
            self.assertViewNotAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, self.pages, self.site), [])

    def test_basic_perm(self):
        user = self.get_standard_user()
        user.user_permissions.add(Permission.objects.get(codename='view_page'))
        request = self.get_request(user)

        with self.assertNumQueries(3):
            """
            The queries are:
            PagePermission query (is this page restricted)
            Generic django permission lookup
            content type lookup by permission lookup
            """
            self.assertViewAllowed(self.page, user)

        self.assertEqual(get_visible_nodes(request, self.pages, self.site), self.expected)


class GlobalPermissionTests(CMSTestCase):

    def test_emulate_admin_index(self):
        """ Call methods that emulate the adminsite instance's index.
        This test was basically the reason for the new manager, in light of the
        problem highlighted in ticket #1120, which asserts that giving a user
        no site-specific rights when creating a GlobalPagePermission should
        allow access to all sites.
        """
        # create and then ignore this user.
        superuser = self._create_user("super", is_staff=True, is_active=True,
                                      is_superuser=True)
        superuser.set_password("super")
        superuser.save()

        site_1 = Site.objects.get(pk=1)
        site_2 = Site.objects.create(domain='example2.com', name='example2.com')

        SITES = [site_1, site_2]

        # create 2 staff users
        USERS = [
            self._create_user("staff", is_staff=True, is_active=True),
            self._create_user("staff_2", is_staff=True, is_active=True),
        ]
        for user in USERS:
            user.set_password('staff')
            # reuse the same methods the UserPage form does.
            # Note that it internally calls .save(), as we've not done so.
            save_permissions({
                'can_add_page': True,
                'can_change_page': True,
                'can_delete_page': False
            }, user)

        GlobalPagePermission.objects.create(can_add=True, can_change=True,
                                            can_delete=False, user=USERS[0])
        # we're querying here to ensure that even though we've created two users
        # above, we should have successfully filtered to just one perm.
        self.assertEqual(1, GlobalPagePermission.objects.with_user(USERS[0]).count())

        # this will confirm explicit permissions still work, by adding the first
        # site instance to the many2many relationship 'sites'
        GlobalPagePermission.objects.create(can_add=True, can_change=True,
                                            can_delete=False,
                                            user=USERS[1]).sites.add(SITES[0])
        self.assertEqual(1, GlobalPagePermission.objects.with_user(USERS[1]).count())

        create_page(title="master", template="nav_playground.html",
                    language="en", in_navigation=True, slug='/')

        with self.settings(CMS_PERMISSION=True):
            # for all users, they should have access to site 1
            request = RequestFactory().get(path='/')
            request.session = {'cms_admin_site': site_1.pk}
            request.current_page = None
            for user in USERS:
                request.user = user
                # Note, the query count is inflated by doing additional lookups
                # because there's a site param in the request.
                # max_queries = 5 for >dj21 because it's introduce default view permissions
                max_queries = 5
                with self.assertNumQueries(FuzzyInt(3, max_queries)):
                    # internally this calls PageAdmin.has_[add|change|delete|view]_permission()
                    expected_perms = {'add': True, 'change': True, 'delete': False}
                    expected_perms.update({'view': False})  # Why
                    self.assertEqual(expected_perms, site._registry[PageContent].get_model_perms(request))

            # can't use the above loop for this test, as we're testing that
            # user 1 has access, but user 2 does not, as they are only assigned
            # to site 1
            request = RequestFactory().get(path='/')
            request.session = {'cms_admin_site': site_2.pk}
            request.current_page = None

            # Refresh internal user cache
            USERS[0] = self.reload(USERS[0])
            USERS[1] = self.reload(USERS[1])

            # As before, the query count is inflated by doing additional lookups
            # because there's a site param in the request
            with self.assertNumQueries(FuzzyInt(5, 15)):
                # this user shouldn't have access to site 2
                request.user = USERS[1]
                expected_perms = {'add': False, 'change': False, 'delete': False}
                expected_perms.update({'view': False})
                self.assertEqual(expected_perms, site._registry[PageContent].get_model_perms(request))
                # but, going back to the first user, they should.
                request = RequestFactory().get('/', data={'site__exact': site_2.pk})
                request.user = USERS[0]
                request.current_page = None
                request.session = {}
                expected_perms = {'add': True, 'change': True, 'delete': False}
                expected_perms.update({'view': False})
                self.assertEqual(expected_perms, site._registry[PageContent].get_model_perms(request))

    def test_has_page_add_permission_with_target(self):
        page = create_page('Test', 'nav_playground.html', 'en')
        user = self._create_user('user')
        request = RequestFactory().get('/', data={'target': page.pk})
        request.session = {}
        request.user = user
        has_perm = site._registry[Page].has_add_permission(request)
        self.assertFalse(has_perm)
