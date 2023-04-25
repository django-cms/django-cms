from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from cms.tests.test_menu_page_viewperm import ViewPermissionTests

__all__ = [
    'ViewPermissionComplexMenuStaffNodeTests',
]


@override_settings(
    CMS_PERMISSION=True,
    CMS_PUBLIC_FOR='staff',
)
class ViewPermissionComplexMenuStaffNodeTests(ViewPermissionTests):
    """
    Test CMS_PUBLIC_FOR=staff group access and menu nodes rendering
    """

    def test_public_pages_anonymous_norestrictions(self):
        """
        All pages are INVISIBLE to an anonymous user
        """
        all_pages = self._setup_tree_pages()
        granted = []
        self.assertGrantedVisibility(all_pages, granted)

    def test_public_menu_anonymous_user(self):
        """
        Anonymous sees nothing, as he is no staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = []
        self.assertGrantedVisibility(all_pages, granted)

    def test_node_staff_access_page_and_children_group_1(self):
        """
        simulate behaviour of group b member
        group_b_ACCESS_PAGE_AND_CHILDREN to page_b
        staff user
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
                   'page_b',
                   'page_b_a',
                   'page_b_b',
                   'page_b_c',
                   'page_b_d',
                   'page_c',
                   'page_c_a',
                   'page_c_b',
                   'page_d_a',
                   'page_d_b',
                   'page_d_c',
                   'page_d_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_1')
        # user 1 is member of group_b_access_page_and_children

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_1@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_1')

        urls = self.get_url_dict(all_pages)

        # call /
        self.assertViewAllowed(urls["/en/page_b/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_c/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_a/"], user)

    def test_node_staff_access_page_and_children_group_1_no_staff(self):
        """
        simulate behaviour of group b member
        group_b_ACCESS_PAGE_AND_CHILDREN to page_b
        no staff user
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = [
                   'page_b',
                   'page_b_a',
                   'page_b_b',
                   'page_b_c',
                   'page_b_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_1_nostaff')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_1_nostaff@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_1_nostaff')

        urls = self.get_url_dict(all_pages)
        self.assertViewAllowed(urls["/en/page_b/page_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_c/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_d/"], user)
        self.assertViewNotAllowed(urls["/en/page_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_a/"], user)

    def test_node_staff_access_children_group_2(self):
        """
        simulate behaviour of group 2 member
        GROUPNAME_2 = 'group_b_b_ACCESS_CHILDREN'
        to page_b_b and user is staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
                   'page_b_b_a',
                   'page_b_b_b',
                   'page_b_b_c',
                   'page_c',
                   'page_c_a',
                   'page_c_b',
                   'page_d_a',
                   'page_d_b',
                   'page_d_c',
                   'page_d_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_2')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_2@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_2')

        urls = self.get_url_dict(all_pages)

        self.assertViewNotAllowed(urls['/en/page_b/'], user)
        self.assertViewNotAllowed(urls['/en/page_b/page_b_b/'], user)
        self.assertViewAllowed(urls['/en/page_b/page_b_b/page_b_b_a/'], user)
        self.assertViewAllowed(urls['/en/page_b/page_b_b/page_b_b_b/'], user)
        self.assertViewNotAllowed(urls['/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/'], user)
        self.assertViewNotAllowed(urls['/en/page_d/'], user)
        self.assertViewAllowed(urls['/en/page_d/page_d_a/'], user)
#
    def test_node_staff_access_children_group_2_nostaff(self):
        """
        simulate behaviour of group 2 member
        GROUPNAME_2 = 'group_b_b_ACCESS_CHILDREN'
        to page_b_b and user is no staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_b_b_a',
                   'page_b_b_b',
                   'page_b_b_c',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_2_nostaff')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_2_nostaff@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_2_nostaff')

        urls = self.get_url_dict(all_pages)
        # member of group that has access to this page
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_a/"], user)

    def test_node_staff_access_page_and_descendants_group_3(self):
        """
        simulate behaviour of group 3 member
        group_b_ACCESS_PAGE_AND_DESCENDANTS to page_b
        and user is staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
                   'page_b',
                   'page_b_a',
                   'page_b_b',
                   'page_b_b_a',
                   'page_b_b_a_a',
                   'page_b_b_b',
                   'page_b_b_c',
                   'page_b_c',
                   'page_b_d',
                   'page_b_d_a',
                   'page_b_d_b',
                   'page_b_d_c',
                   'page_c',
                   'page_c_a',
                   'page_c_b',
                   'page_d_a',
                   'page_d_b',
                   'page_d_c',
                   'page_d_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_3')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_3@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_3')

        urls = self.get_url_dict(all_pages)
        url = self.get_pages_root()
        self.assertViewAllowed(urls[url], user)
        self.assertViewAllowed(urls["/en/page_b/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_c/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_d/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"], user)
        self.assertViewAllowed(urls["/en/page_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_a/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_b/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_c/"], user)

    def test_node_staff_access_page_and_descendants_group_3_nostaff(self):
        """
        simulate behaviour of group 3 member
        group_b_ACCESS_PAGE_AND_DESCENDANTS to page_b
        user is not staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_b',
                   'page_b_a',
                   'page_b_b',
                   'page_b_b_a',
                   'page_b_b_a_a',
                   'page_b_b_b',
                   'page_b_b_c',
                   'page_b_c',
                   'page_b_d',
                   'page_b_d_a',
                   'page_b_d_b',
                   'page_b_d_c',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_3_nostaff')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_3_nostaff@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_3_nostaff')

        urls = self.get_url_dict(all_pages)
        # call /
        url = self.get_pages_root()
        self.assertViewNotAllowed(urls[url], user)
        self.assertViewAllowed(urls["/en/page_b/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_c/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_d/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_c/"], user)

    def test_node_staff_access_descendants_group_4(self):
        """
        simulate behaviour of group 4 member
        group_b_b_ACCESS_DESCENDANTS to page_b_b
        user is staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
                   'page_b_b_a',
                   'page_b_b_a_a',
                   'page_b_b_b',
                   'page_b_b_c',
                   'page_c',
                   'page_c_a',
                   'page_c_b',
                   'page_d_a',
                   'page_d_b',
                   'page_d_c',
                   'page_d_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_4')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_4@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_4')

        urls = self.get_url_dict(all_pages)
        # call /
        url = self.get_pages_root()
        self.assertViewAllowed(urls[url], user)
        self.assertViewNotAllowed(urls["/en/page_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_d/"], user)
        # not a direct child
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"], user)
        self.assertViewAllowed(urls["/en/page_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_a/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_b/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_c/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_d/"], user)

    def test_node_staff_access_descendants_group_4_nostaff(self):
        """
        simulate behaviour of group 4 member
        group_b_b_ACCESS_DESCENDANTS to page_b_b
        user is no staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = [
                   'page_b_b_a',
                   'page_b_b_a_a',
                   'page_b_b_b',
                   'page_b_b_c',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_4_nostaff')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_4_nostaff@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_4_nostaff')

        urls = self.get_url_dict(all_pages)
        url = self.get_pages_root()
        self.assertViewNotAllowed(urls[url], user)
        self.assertViewNotAllowed(urls["/en/page_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_d/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_d/"], user)

    def test_node_staff_access_page_group_5(self):
        """
        simulate behaviour of group b member
        group_d_ACCESS_PAGE to page_d
        user is staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
                   'page_c',
                   'page_c_a',
                   'page_c_b',
                   'page_d',
                   'page_d_a',
                   'page_d_b',
                   'page_d_c',
                   'page_d_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_5')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_5@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_5')

        urls = self.get_url_dict(all_pages)
        url = self.get_pages_root()
        self.assertViewAllowed(urls[url], user)
        self.assertViewNotAllowed(urls["/en/page_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_d/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"], user)
        self.assertViewAllowed(urls["/en/page_c/"], user)
        self.assertViewAllowed(urls["/en/page_d/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_a/"], user)

    def test_node_staff_access_page_group_5_nostaff(self):
        """
        simulate behaviour of group b member
        group_d_ACCESS_PAGE to page_d
        nostaff user
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_d',]
        self.assertGrantedVisibility(all_pages, granted, username='user_5_nostaff')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_5_nostaff@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_5_nostaff')

        urls = self.get_url_dict(all_pages)
        url = self.get_pages_root()
        self.assertViewNotAllowed(urls[url], user)
        self.assertViewAllowed(urls["/en/page_d/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_d/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_c/"], user)
        self.assertViewAllowed(urls["/en/page_d/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_c/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/page_d_d/"], user)
