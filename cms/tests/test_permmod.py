from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.sites.models import Site
from django.db.models import Q
from django.test.client import RequestFactory
from django.test.utils import override_settings

from cms.admin.forms import save_permissions
from cms.api import add_plugin, assign_user_to_page, create_page, create_page_user, publish_page
from cms.cms_menus import get_visible_nodes
from cms.models import ACCESS_PAGE, CMSPlugin, Page, Title
from cms.models.permissionmodels import (
    ACCESS_DESCENDANTS,
    ACCESS_PAGE_AND_DESCENDANTS,
    GlobalPagePermission,
    PagePermission,
)
from cms.test_utils.testcases import URL_CMS_PAGE_ADD, CMSTestCase
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.utils import get_current_site
from cms.utils.page_permissions import user_can_publish_page, user_can_view_page


def fake_tree_attrs(page):
    page.depth = 1
    page.path = '0001'
    page.numchild = 0


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
    #TODO: Split this test case into one that tests publish functionality, and
    #TODO: one that tests permission inheritance. This is too complex.

    def setUp(self):
        # create super user
        self.user_super = self._create_user("super", is_staff=True,
                                            is_superuser=True)
        self.user_staff = self._create_user("staff", is_staff=True,
                                            add_default_permissions=True)
        self.add_permission(self.user_staff, 'publish_page')
        self.user_master = self._create_user("master", is_staff=True,
                                             add_default_permissions=True)
        self.add_permission(self.user_master, 'publish_page')
        self.user_slave = self._create_user("slave", is_staff=True,
                                            add_default_permissions=True)
        self.user_normal = self._create_user("normal", is_staff=False)
        self.user_normal.user_permissions.add(
            Permission.objects.get(codename='publish_page'))

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
            page_b = create_page("pageB", "nav_playground.html", "en", created_by=self.user_super)
            # Normal user

            # it's allowed for the normal user to view the page
            assign_user_to_page(page_b, self.user_normal, can_view=True)

            # create page_a - sample page from master

            page_a = create_page("pageA", "nav_playground.html", "en",
                                 created_by=self.user_super)
            assign_user_to_page(page_a, self.user_master,
                                can_add=True, can_change=True, can_delete=True, can_publish=True,
                                can_move_page=True)

            # publish after creating all drafts
            publish_page(self.home_page, self.user_super, 'en')

            publish_page(self.master_page, self.user_super, 'en')

            self.page_b = publish_page(page_b, self.user_super, 'en')

    def _add_plugin(self, user, page):
        """
        Add a plugin using the test client to check for permissions.
        """
        with self.login_user_context(user):
            placeholder = page.placeholders.all()[0]
            post_data = {
                'body': 'Test'
            }
            endpoint = self.get_add_plugin_uri(placeholder, 'TextPlugin')
            response = self.client.post(endpoint, post_data)
            self.assertEqual(response.status_code, 302)
            return response.content.decode('utf8')

    def test_super_can_add_page_to_root(self):
        with self.login_user_context(self.user_super):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 200)

    def test_master_cannot_add_page_to_root(self):
        with self.login_user_context(self.user_master):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 403)

    def test_slave_cannot_add_page_to_root(self):
        with self.login_user_context(self.user_slave):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 403)

    def test_slave_can_add_page_under_slave_home(self):
        with self.login_user_context(self.user_slave):
            # move to admin.py?
            # url = URL_CMS_PAGE_ADD + "?target=%d&position=last-child" % slave_page.pk

            # can he even access it over get?
            # response = self.client.get(url)
            # self.assertEqual(response.status_code, 200)

            # add page
            page = create_page("page", "nav_playground.html", "en",
                               parent=self.slave_page, created_by=self.user_slave)
            # adds user_slave as page moderator for this page
            # public model shouldn't be available yet, because of the moderation
            # moderators and approval ok?

            # must not have public object yet
            self.assertFalse(page.publisher_public)

            self.assertObjectExist(Title.objects, slug="page")
            self.assertObjectDoesNotExist(Title.objects.public(), slug="page")

            self.assertTrue(user_can_publish_page(self.user_slave, page))

            # publish as slave, published as user_master before
            publish_page(page, self.user_slave, 'en')
            # user_slave is moderator for this page
            # approve / publish as user_slave
            # user master should be able to approve as well

    @override_settings(
        CMS_PLACEHOLDER_CONF={
            'col_left': {
                'default_plugins': [
                    {
                        'plugin_type': 'TextPlugin',
                        'values': {
                            'body': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Culpa, repellendus, delectus, quo quasi ullam inventore quod quam aut voluptatum aliquam voluptatibus harum officiis officia nihil minus unde accusamus dolorem repudiandae.'
                        },
                    },
                ]
            },
        },
    )
    def test_default_plugins(self):
        with self.login_user_context(self.user_slave):
            self.assertEqual(CMSPlugin.objects.count(), 0)
            response = self.client.get(self.slave_page.get_absolute_url(), {'edit': 1})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(CMSPlugin.objects.count(), 1)

    def test_page_added_by_slave_can_be_published_by_user_master(self):
        # add page
        page = create_page("page", "nav_playground.html", "en",
                           parent=self.slave_page, created_by=self.user_slave)
        # same as test_slave_can_add_page_under_slave_home

        # must not have public object yet
        self.assertFalse(page.publisher_public)

        self.assertTrue(user_can_publish_page(self.user_master, page))
        # should be True user_master should have publish permissions for children as well
        publish_page(self.slave_page, self.user_master, 'en')
        page = publish_page(page, self.user_master, 'en')
        self.assertTrue(page.publisher_public_id)
        # user_master is moderator for top level page / but can't approve descendants?
        # approve / publish as user_master
        # user master should be able to approve descendants

    def test_super_can_add_plugin(self):
        self._add_plugin(self.user_super, page=self.slave_page)

    def test_master_can_add_plugin(self):
        self._add_plugin(self.user_master, page=self.slave_page)

    def test_slave_can_add_plugin(self):
        self._add_plugin(self.user_slave, page=self.slave_page)

    def test_subtree_needs_approval(self):
        # create page under slave_page
        page = create_page("parent", "nav_playground.html", "en",
                           parent=self.home_page)
        self.assertFalse(page.publisher_public)

        # create subpage under page
        subpage = create_page("subpage", "nav_playground.html", "en", parent=page, published=False)

        # publish both of them in reverse order
        subpage = publish_page(subpage, self.user_master, 'en')

        # subpage should not be published, because parent is not published
        self.assertNeverPublished(subpage)

        # publish page (parent of subage)
        page = publish_page(page, self.user_master, 'en')
        self.assertPublished(page)
        self.assertNeverPublished(subpage)

        subpage = publish_page(subpage, self.user_master, 'en')

        self.assertPublished(subpage)

    def test_subtree_with_super(self):
        # create page under root
        page = create_page("page", "nav_playground.html", "en")
        self.assertFalse(page.publisher_public)

        # create subpage under page
        subpage = create_page("subpage", "nav_playground.html", "en",
                              parent=page)
        self.assertFalse(subpage.publisher_public)

        # tree id must be the same
        self.assertEqual(page.node.path[0:4], subpage.node.path[0:4])

        # publish both of them
        page = self.reload(page)
        page = publish_page(page, self.user_super, 'en')
        # reload subpage, there were an path change
        subpage = self.reload(subpage)
        self.assertEqual(page.node.path[0:4], subpage.node.path[0:4])

        subpage = publish_page(subpage, self.user_super, 'en')
        # tree id must stay the same
        self.assertEqual(page.node.path[0:4], subpage.node.path[0:4])

    def test_super_add_page_to_root(self):
        """Create page which is not under moderation in root, and check if
        some properties are correct.
        """
        # create page under root
        page = create_page("page", "nav_playground.html", "en")

        # public must not exist
        self.assertFalse(page.publisher_public)

    def test_plugins_get_published(self):
        # create page under root
        page = create_page("page", "nav_playground.html", "en")
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, "TextPlugin", "en", body="test")
        # public must not exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        publish_page(page, self.user_super, 'en')
        self.assertEqual(CMSPlugin.objects.all().count(), 2)

    def test_remove_plugin_page_under_moderation(self):
        # login as slave and create page
        page = create_page("page", "nav_playground.html", "en", parent=self.slave_page)

        # add plugin
        placeholder = page.placeholders.all()[0]
        plugin = add_plugin(placeholder, "TextPlugin", "en", body="test")

        # publish page
        page = self.reload(page)
        page = publish_page(page, self.user_slave, 'en')

        # only the draft plugin should exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)

        # master approves and publishes the page
        # first approve slave-home
        slave_page = self.reload(self.slave_page)
        publish_page(slave_page, self.user_master, 'en')
        page = self.reload(page)
        page = publish_page(page, self.user_master, 'en')

        # draft and public plugins should now exist
        self.assertEqual(CMSPlugin.objects.all().count(), 2)

        # login as slave and delete the plugin - should require moderation
        with self.login_user_context(self.user_slave):
            plugin_data = {
                'plugin_id': plugin.pk
            }
            endpoint = self.get_delete_plugin_uri(plugin)
            response = self.client.post(endpoint, plugin_data)
            self.assertEqual(response.status_code, 302)

            # there should only be a public plugin - since the draft has been deleted
            self.assertEqual(CMSPlugin.objects.all().count(), 1)

            page = self.reload(page)

            # login as super user and approve/publish the page
            publish_page(page, self.user_super, 'en')

            # there should now be 0 plugins
            self.assertEqual(CMSPlugin.objects.all().count(), 0)

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
            user_global.save() # Prevent is_staff permission
            global_page = create_page("global", "nav_playground.html", "en",
                                      published=True)
            # Removed call since global page user doesn't have publish permission
            #global_page = publish_page(global_page, user_global)
            # it's allowed for the normal user to view the page
            assign_user_to_page(global_page, user_global,
                                global_permission=True, can_view=True)

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


@override_settings(CMS_PERMISSION=True)
class PatricksMoveTest(CMSTestCase):
    """
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
                      move/publish/moderate this page and its descendants
                    - `master` user want to moderate this page and all descendants

        4. `pageA`:
            - created by super
            - master can add/change/delete on it and descendants
    """

    def setUp(self):
        # create super user
        self.user_super = self._create_user("super", True, True)

        with self.login_user_context(self.user_super):
            self.home_page = create_page("home", "nav_playground.html", "en",
                                         created_by=self.user_super)

            # master page & master user

            self.master_page = create_page("master", "nav_playground.html", "en")

            # create master user
            self.user_master = self._create_user("master", True)
            self.add_permission(self.user_master, 'change_page')
            self.add_permission(self.user_master, 'publish_page')
            #self.user_master = create_page_user(self.user_super, master, grant_all=True)

            # assign master user under home page
            assign_user_to_page(self.home_page, self.user_master,
                                grant_on=ACCESS_DESCENDANTS, grant_all=True)

            # and to master page
            assign_user_to_page(self.master_page, self.user_master, grant_all=True)

            # slave page & slave user

            self.slave_page = create_page("slave-home", "nav_playground.html", "en",
                                          parent=self.master_page, created_by=self.user_super)
            slave = self._create_user("slave", True)
            self.user_slave = create_page_user(self.user_super, slave, can_add_page=True,
                                               can_change_page=True, can_delete_page=True)

            assign_user_to_page(self.slave_page, self.user_slave, grant_all=True)

            # create page_a - sample page from master

            page_a = create_page("pageA", "nav_playground.html", "en",
                                 created_by=self.user_super)
            assign_user_to_page(page_a, self.user_master,
                                can_add=True, can_change=True, can_delete=True, can_publish=True,
                                can_move_page=True)

            # publish after creating all drafts
            publish_page(self.home_page, self.user_super, 'en')
            publish_page(self.master_page, self.user_super, 'en')

        with self.login_user_context(self.user_slave):
            # 000200010001
            self.pa = create_page("pa", "nav_playground.html", "en", parent=self.slave_page)
            # 000200010002
            self.pb = create_page("pb", "nav_playground.html", "en", parent=self.pa, position="right")
            # 000200010003
            self.pc = create_page("pc", "nav_playground.html", "en", parent=self.pb, position="right")

            self.pd = create_page("pd", "nav_playground.html", "en", parent=self.pb)
            self.pe = create_page("pe", "nav_playground.html", "en", parent=self.pd, position="right")

            self.pf = create_page("pf", "nav_playground.html", "en", parent=self.pe)
            self.pg = create_page("pg", "nav_playground.html", "en", parent=self.pf, position="right")
            self.ph = create_page("ph", "nav_playground.html", "en", parent=self.pf, position="right")

            self.assertFalse(self.pg.publisher_public)

            # login as master for approval
            self.slave_page = self.slave_page.reload()

            publish_page(self.slave_page, self.user_master, 'en')

            # publish and approve them all
            publish_page(self.pa, self.user_master, 'en')
            publish_page(self.pb, self.user_master, 'en')
            publish_page(self.pc, self.user_master, 'en')
            publish_page(self.pd, self.user_master, 'en')
            publish_page(self.pe, self.user_master, 'en')
            publish_page(self.pf, self.user_master, 'en')
            publish_page(self.pg, self.user_master, 'en')
            publish_page(self.ph, self.user_master, 'en')
            self.reload_pages()

    def reload_pages(self):
        self.pa = self.pa.reload()
        self.pb = self.pb.reload()
        self.pc = self.pc.reload()
        self.pd = self.pd.reload()
        self.pe = self.pe.reload()
        self.pf = self.pf.reload()
        self.pg = self.pg.reload()
        self.ph = self.ph.reload()


    def test_patricks_move(self):
        """

        Tests permmod when moving trees of pages.

        1. build following tree (master node is approved and published)

                 slave-home
                /    |    \
               A     B     C
                   /  \
                  D    E
                    /  |  \
                   F   G   H

        2. perform move operations:
            1. move G under C
            2. move E under G

                 slave-home
                /    |    \
               A     B     C
                   /        \
                  D          G
                              \
                               E
                             /   \
                            F     H

        3. approve nodes in following order:
            1. approve H
            2. approve G
            3. approve E
            4. approve F
        """
        self.assertEqual(self.pg.node.parent, self.pe.node)
        # perform moves under slave...
        self.move_page(self.pg, self.pc)
        self.reload_pages()
        # page is now under PC
        self.assertEqual(self.pg.node.parent, self.pc.node)
        self.assertEqual(self.pg.get_absolute_url(), self.pg.publisher_public.get_absolute_url())
        self.move_page(self.pe, self.pg)
        self.reload_pages()
        self.assertEqual(self.pe.node.parent, self.pg.node)
        self.ph = self.ph.reload()
        # check urls - they should stay be the same now after the move
        self.assertEqual(
            self.pg.publisher_public.get_absolute_url(),
            self.pg.get_absolute_url()
        )
        self.assertEqual(
            self.ph.publisher_public.get_absolute_url(),
            self.ph.get_absolute_url()
        )

        # check if urls are correct after move
        self.assertEqual(
            self.pg.publisher_public.get_absolute_url(),
            '%smaster/slave-home/pc/pg/' % self.get_pages_root()
        )
        self.assertEqual(
            self.ph.publisher_public.get_absolute_url(),
            '%smaster/slave-home/pc/pg/pe/ph/' % self.get_pages_root()
        )


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


class PublicViewPermissionTests(RestrictedViewPermissionTests):
    """ Run the same tests as before, but on the public page instead. """

    def setUp(self):
        super().setUp()
        self.page.publish('en')
        self.pages = [self.page.publisher_public]
        self.expected = [self.page.publisher_public]


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
            # re-use the same methods the UserPage form does.
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

        homepage = create_page(title="master", template="nav_playground.html",
                               language="en", in_navigation=True, slug='/')
        publish_page(page=homepage, user=superuser, language='en')

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
                    expected_perms.update({'view': True})
                    self.assertEqual(expected_perms, site._registry[Page].get_model_perms(request))

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
                self.assertEqual(expected_perms, site._registry[Page].get_model_perms(request))
                # but, going back to the first user, they should.
                request = RequestFactory().get('/', data={'site__exact': site_2.pk})
                request.user = USERS[0]
                request.current_page = None
                request.session = {}
                expected_perms = {'add': True, 'change': True, 'delete': False}
                expected_perms.update({'view': True})
                self.assertEqual(expected_perms, site._registry[Page].get_model_perms(request))

    def test_has_page_add_permission_with_target(self):
        page = create_page('Test', 'nav_playground.html', 'en')
        user = self._create_user('user')
        request = RequestFactory().get('/', data={'target': page.pk})
        request.session = {}
        request.user = user
        has_perm = site._registry[Page].has_add_permission(request)
        self.assertFalse(has_perm)
