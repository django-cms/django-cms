from html import unescape

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import override as force_language

from cms.admin import forms
from cms.admin.forms import (
    DuplicatePageForm,
    GlobalPagePermissionAdminForm,
    PagePermissionInlineAdminForm,
    PageUserGroupForm,
    ViewRestrictionInlineAdminForm,
    get_permission_accessor,
)
from cms.api import assign_user_to_page, create_page, create_page_content
from cms.forms.fields import PageSelectFormField
from cms.forms.utils import (
    get_page_choices,
    get_site_choices,
    update_site_and_page_choices,
)
from cms.forms.widgets import ApplicationConfigSelect
from cms.models import ACCESS_PAGE, ACCESS_PAGE_AND_CHILDREN
from cms.test_utils.testcases import (
    URL_CMS_PAGE_ADVANCED_CHANGE,
    URL_CMS_PAGE_PERMISSIONS,
    CMSTestCase,
)
from cms.utils.permissions import current_user


class Mock_PageSelectFormField(PageSelectFormField):
    def __init__(self, required=False):
        # That's to have a proper mock object, without having to resort
        # to dirtier tricks. We want to test *just* compress here.
        self.required = required
        self.error_messages = {}
        self.error_messages["invalid_page"] = "Invalid_page"


class FormsTestCase(CMSTestCase):
    def setUp(self):
        cache.clear()
        self.site = Site.objects.get_current()

    def test_get_site_choices(self):
        result = get_site_choices()
        self.assertEqual(result, [])

    def test_get_page_choices(self):
        result = get_page_choices()
        self.assertEqual(result, [("", "----")])

    def test_page_choices_draft_only(self):
        """
        The page choices should always use draft ids
        """
        pages = [
            create_page("0001", "nav_playground.html", "en"),
            create_page("0002", "nav_playground.html", "en"),
            create_page("0003", "nav_playground.html", "en"),
            create_page("0004", "nav_playground.html", "en"),
        ]

        expected = [("", "----"), (self.site.name, [(page.pk, page.get_title("en", fallback=False)) for page in pages])]
        self.assertSequenceEqual(get_page_choices("en"), expected)

    def test_get_page_choices_with_multiple_translations(self):
        pages = [
            create_page("0001", "nav_playground.html", "en"),
            create_page("0002", "nav_playground.html", "en"),
            create_page("0003", "nav_playground.html", "en"),
            create_page("0004", "nav_playground.html", "en"),
        ]
        languages = ["de", "fr"]

        for page in pages:
            for language in languages:
                title = page.get_title("en")
                create_page_content(language, title, page=page)

        for language in ["en"] + languages:
            expected = [
                ("", "----"),
                (self.site.name, [(page.pk, page.get_title(language, fallback=False)) for page in pages]),
            ]

            with force_language(language):
                self.assertSequenceEqual(get_page_choices(), expected)

    def test_get_site_choices_without_moderator(self):
        result = get_site_choices()
        self.assertEqual(result, [])

    def test_get_site_choices_without_moderator_with_superuser(self):
        # boilerplate (creating a page)
        User = get_user_model()

        fields = dict(is_staff=True, is_active=True, is_superuser=True, email="super@super.com")

        if User.USERNAME_FIELD != "email":
            fields[User.USERNAME_FIELD] = "super"

        user_super = User(**fields)
        user_super.set_password(getattr(user_super, User.USERNAME_FIELD))
        user_super.save()
        with self.login_user_context(user_super):
            create_page("home", "nav_playground.html", "en", created_by=user_super)
            # The proper test
            result = get_site_choices()
            self.assertEqual(result, [(1, "example.com")])

    def test_compress_function_raises_when_page_is_none(self):
        raised = False
        try:
            fake_field = Mock_PageSelectFormField(required=True)
            data_list = (0, None)  # (site_id, page_id) dsite-id is not used
            fake_field.compress(data_list)
            self.fail("compress function didn't raise!")
        except forms.ValidationError:
            raised = True
        self.assertTrue(raised)

    def test_compress_function_returns_none_when_not_required(self):
        fake_field = Mock_PageSelectFormField(required=False)
        data_list = (0, None)  # (site_id, page_id) dsite-id is not used
        result = fake_field.compress(data_list)
        self.assertEqual(result, None)

    def test_compress_function_returns_none_when_no_data_list(self):
        fake_field = Mock_PageSelectFormField(required=False)
        data_list = None
        result = fake_field.compress(data_list)
        self.assertEqual(result, None)

    def test_compress_function_gets_a_page_when_one_exists(self):
        # boilerplate (creating a page)
        User = get_user_model()

        fields = dict(is_staff=True, is_active=True, is_superuser=True, email="super@super.com")

        if User.USERNAME_FIELD != "email":
            fields[User.USERNAME_FIELD] = "super"

        user_super = User(**fields)
        user_super.set_password(getattr(user_super, User.USERNAME_FIELD))
        user_super.save()

        with self.login_user_context(user_super):
            home_page = create_page("home", "nav_playground.html", "en", created_by=user_super)
            # The actual test
            fake_field = Mock_PageSelectFormField()
            data_list = (0, home_page.pk)  # (site_id, page_id) dsite-id is not used
            result = fake_field.compress(data_list)
            self.assertEqual(home_page, result)

    def test_update_site_and_page_choices(self):
        Site.objects.all().delete()
        site = Site.objects.create(domain="http://www.django-cms.org", name="Django CMS", pk=1)
        page1 = create_page("Page 1", "nav_playground.html", "en", site=site)
        page2 = create_page("Page 2", "nav_playground.html", "de", site=site)
        page3 = create_page("Page 3", "nav_playground.html", "en", site=site, parent=page1)
        # Check for injection attacks
        page4 = create_page(
            'Page 4<script>alert("bad-things");</script>', "nav_playground.html", "en", site=site, parent=page1
        )
        # enforce the choices to be casted to a list
        site_choices, page_choices = (list(bit) for bit in update_site_and_page_choices("en"))
        self.assertEqual(
            page_choices,
            [
                ("", "----"),
                (
                    site.name,
                    [
                        (page1.pk, "Page 1"),
                        (page3.pk, "&nbsp;&nbsp;Page 3"),
                        (page4.pk, "&nbsp;&nbsp;Page 4&lt;script&gt;alert(&quot;bad-things&quot;);&lt;/script&gt;"),
                        (page2.pk, "Page 2"),
                    ],
                ),
            ],
        )
        self.assertEqual(site_choices, [(site.pk, site.name)])

    def test_app_config_select_escaping(self):
        class FakeAppConfig:
            def __init__(self, pk, config):
                self.pk = pk
                self.config = config

            def __str__(self):
                return self.config

        class FakeApp:
            def __init__(self, name, configs=()):
                self.name = name
                self.configs = configs

            def __str__(self):
                return self.name

            def get_configs(self):
                return self.configs

            def get_config_add_url(self):
                return "/fake/url/"

        GoodApp = FakeApp(
            "GoodApp",
            [
                FakeAppConfig(1, "good-app-one-config"),
                FakeAppConfig(2, "good-app-two-config"),
            ],
        )

        BadApp = FakeApp(
            "BadApp",
            [
                FakeAppConfig(1, "bad-app-one-config"),
                FakeAppConfig(2, 'bad-app-two-config<script>alert("bad-stuff");</script>'),
            ],
        )

        app_configs = {
            GoodApp: GoodApp,
            BadApp: BadApp,
        }

        app_config_select = ApplicationConfigSelect(app_configs=app_configs)
        output = app_config_select.render("application_configurations", 1)
        self.assertFalse('<script>alert("bad-stuff");</script>' in output)
        self.assertTrue('\\u003Cscript\\u003Ealert(\\"bad-stuff\\");\\u003C/script\\u003E' in output)

    def test_move_page_form(self):
        """Test the MovePageForm validation and behavior"""
        # Create a basic page structure
        parent1 = create_page("Parent 1", "nav_playground.html", "en")
        parent2 = create_page("Parent 2", "nav_playground.html", "en")
        child1 = create_page("Child 1", "nav_playground.html", "en", parent=parent1)

        # Test valid move between parents
        data = {
            "target": parent2.pk,
            "position": "0",  # first-child
            "site": self.site.pk,
        }
        form = forms.MovePageForm(data=data, page=child1, site=self.site)
        self.assertTrue(form.is_valid(), form.errors)

        # Test moving page with same slug under different parents
        child2 = create_page("Child 2", "nav_playground.html", "en", parent=parent2)
        data = {
            "target": parent1.pk,
            "position": "0",  # first-child
            "site": self.site.pk,
        }
        form = forms.MovePageForm(data=data, page=child2, site=self.site)
        self.assertTrue(form.is_valid(), form.errors)

        # Test moving page to a position that would create duplicate slug
        child3 = create_page("Child 1", "nav_playground.html", "en", parent=parent2)  # Same slug as child1
        data = {
            "target": parent1.pk,
            "position": "0",  # first-child
            "site": self.site.pk,
        }
        form = forms.MovePageForm(data=data, page=child3, site=self.site)
        self.assertFalse(form.is_valid())
        self.assertIn("You cannot have two pages with the same slug", str(form.errors["__all__"]))

        # Test moving homepage
        homepage = create_page("Home", "nav_playground.html", "en")
        homepage.set_as_homepage()
        data = {
            "target": parent1.pk,
            "position": "0",  # first-child
            "site": self.site.pk,
        }
        form = forms.MovePageForm(data=data, page=homepage, site=self.site)
        self.assertFalse(form.is_valid())
        self.assertIn("You can&#x27;t move the home page inside another page", str(form.errors["target"]))

    def test_move_page_form_positions(self):
        """Test different position options in MovePageForm"""
        parent = create_page("Parent", "nav_playground.html", "en")
        child1 = create_page("Child 1", "nav_playground.html", "en", parent=parent)
        child2 = create_page("Child 2", "nav_playground.html", "en", parent=parent)

        positions = (
            ("0", "first-child"),  # First child of target
            ("1", "last-child"),  # Last child of target
            ("2", "left"),  # Left sibling of target
            ("3", "right"),  # Right sibling of target
        )

        for position_id, position_name in positions:
            data = {
                "target": child2.pk,
                "position": position_id,  # Use the numeric position ID
                "site": self.site.pk,
            }
            form = forms.MovePageForm(data=data, page=child1, site=self.site)
            self.assertTrue(
                form.is_valid(), f"Form should be valid for position {position_name}, errors: {form.errors}"
            )

    def test_move_page_form_sibling_slug_collision(self):
        """Test that pages cannot be moved to create duplicate slugs at the same level"""
        # Create two separate parent pages
        parent1 = create_page("Parent 1", "nav_playground.html", "en", slug="parent-1")
        parent2 = create_page("Parent 2", "nav_playground.html", "en", slug="parent-2")

        # Create a child under parent1 with slug "test"
        create_page("Test Page", "nav_playground.html", "en", slug="test", parent=parent1)

        # Create a child under parent2 with the same slug "test" (this is allowed because they have different parents)
        child2 = create_page("Test Page", "nav_playground.html", "en", slug="test", parent=parent2)

        # Try to move child2 to be under parent1 (should fail because child1 is already there with same slug)
        data = {
            "target": parent1.pk,
            "position": 2,  # 2 = first-child position
            "site": self.site.pk,
        }

        form = forms.MovePageForm(data=data, page=child2, site=self.site)
        is_valid = form.is_valid()

        self.assertFalse(is_valid, "Form should be invalid due to slug collision")
        self.assertIn(
            "You cannot have two pages with the same slug",
            str(form.errors["__all__"]),
            "Form should report slug collision error",
        )

    def test_move_page_form_child_parent_slug_collision(self):
        """Test that pages cannot be moved to create duplicate slugs at the same level"""
        # Create grandparent page
        grandparent = create_page("Grandparent", "nav_playground.html", "en", slug="grandparent")

        # Create parent page
        parent = create_page("Parent", "nav_playground.html", "en", slug="parent", parent=grandparent)

        # Create a child under parent with the same slug
        child = create_page("Child", "nav_playground.html", "en", slug="parent", parent=parent)

        # Try to move child to be on the same level as parent (should fail because parent is already there with same slug)
        data = {
            "target": grandparent.pk,
            "position": 2,  # 2 = first-child position
            "site": self.site.pk,
        }

        form = forms.MovePageForm(data=data, page=child, site=self.site)
        is_valid = form.is_valid()

        self.assertFalse(is_valid, "Form should be invalid due to slug collision")
        self.assertIn(
            "You cannot have two pages with the same slug",
            str(form.errors["__all__"]),
            "Form should report slug collision error",
        )


class PermissionFormTestCase(CMSTestCase):
    def test_permission_forms(self):
        page = create_page("page_b", "nav_playground.html", "en", created_by=self.get_superuser())
        normal_user = self._create_user("randomuser", is_staff=True, add_default_permissions=True)
        assign_user_to_page(page, normal_user, can_view=True, can_change=True)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(URL_CMS_PAGE_ADVANCED_CHANGE % page.pk)
            self.assertEqual(response.status_code, 200)
            response = self.client.get(URL_CMS_PAGE_PERMISSIONS % page.pk)
            self.assertEqual(response.status_code, 200)

        with self.settings(CMS_RAW_ID_USERS=True), current_user(self.get_superuser()):
            data = {
                "page": page.pk,
                "grant_on": "hello",
                "user": normal_user.pk,
            }
            form = PagePermissionInlineAdminForm(data=data, files=None)
            self.assertFalse(form.is_valid())
            data = {
                "page": page.pk,
                "grant_on": ACCESS_PAGE,
                "user": normal_user.pk,
            }
            form = PagePermissionInlineAdminForm(data=data, files=None)
            self.assertTrue(form.is_valid())
            form.save()

            data = {
                "page": page.pk,
                "grant_on": ACCESS_PAGE_AND_CHILDREN,
                "can_add": "1",
                "can_change": "",
                "user": normal_user.pk,
            }
            form = PagePermissionInlineAdminForm(data=data, files=None)

            error_message = (
                "<li>Users can't create a page without permissions "
                "to change the created page. Edit permissions required.</li>"
            )
            self.assertFalse(form.is_valid())
            self.assertTrue(error_message in unescape(str(form.errors)))
            data = {
                "page": page.pk,
                "grant_on": ACCESS_PAGE,
                "can_add": "1",
                "can_change": "1",
                "user": normal_user.pk,
            }
            form = PagePermissionInlineAdminForm(data=data, files=None)
            self.assertFalse(form.is_valid())
            self.assertTrue(
                "<li>Add page permission requires also access to children, or "
                "descendants, otherwise added page can't be changed by its "
                "creator.</li>" in unescape(str(form.errors))
            )

    def test_inlines(self):
        user = self._create_user("randomuser", is_staff=True, add_default_permissions=True)
        current_user = self.get_superuser()
        page = create_page("page_b", "nav_playground.html", "en", created_by=current_user)
        data = {
            "page": page.pk,
            "grant_on": ACCESS_PAGE_AND_CHILDREN,
            "can_view": "True",
            "user": user.pk,
            "group": "",
        }
        form = ViewRestrictionInlineAdminForm(data=data, files=None)
        self.assertTrue(form.is_valid())
        data = {"page": page.pk, "grant_on": ACCESS_PAGE_AND_CHILDREN, "can_view": "True", "group": ""}
        form = GlobalPagePermissionAdminForm(data=data, files=None)
        self.assertFalse(form.is_valid())

        data = {
            "page": page.pk,
            "grant_on": ACCESS_PAGE_AND_CHILDREN,
            "can_view": "True",
            "user": user.pk,
        }
        form = GlobalPagePermissionAdminForm(data=data, files=None)
        self.assertTrue(form.is_valid())

    def test_user_forms(self):
        user = self.get_superuser()

        data = {"name": "test_group"}
        form = PageUserGroupForm(data=data, files=None)
        form._current_user = user
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        form = PageUserGroupForm(data=data, files=None, instance=instance)
        form._current_user = user
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

    def test_page_user_group_form_drops_unauthorized_permissions(self):
        """A delegated manager must not be able to grant a group permissions
        they do not hold themselves, even by POSTing the hidden ``can_*``
        fields that ``get_fieldsets`` never rendered for them (CWE-269).
        """
        # Manager holds change_page but NOT any pagepermission/pageuser perms.
        manager = self._create_user("manager", is_staff=True, permissions=["change_page"])
        self.assertTrue(manager.has_perm("cms.change_page"))
        self.assertFalse(manager.has_perm("cms.change_pagepermission"))

        data = {
            "name": "evil_group",
            "can_change_page": True,           # held by the manager -> must be kept
            "can_change_pagepermission": True,  # NOT held -> must be dropped
            "can_add_pagepermission": True,     # NOT held -> must be dropped
            "can_change_pageuser": True,        # NOT held -> must be dropped
        }
        form = PageUserGroupForm(data=data, files=None)
        form._current_user = manager
        self.assertTrue(form.is_valid(), form.errors)
        group = form.save()

        granted = set(get_permission_accessor(group).values_list("codename", flat=True))
        self.assertIn("change_page", granted)
        self.assertNotIn("change_pagepermission", granted)
        self.assertNotIn("add_pagepermission", granted)
        self.assertNotIn("change_pageuser", granted)

    def test_page_user_group_form_superuser_can_grant_anything(self):
        """A superuser holds every permission, so nothing is dropped."""
        superuser = self.get_superuser()
        data = {
            "name": "trusted_group",
            "can_change_page": True,
            "can_change_pagepermission": True,
        }
        form = PageUserGroupForm(data=data, files=None)
        form._current_user = superuser
        self.assertTrue(form.is_valid(), form.errors)
        group = form.save()

        granted = set(get_permission_accessor(group).values_list("codename", flat=True))
        self.assertIn("change_page", granted)
        self.assertIn("change_pagepermission", granted)


class DuplicatePageFormSecurityTestCase(CMSTestCase):
    def _build_form(self, user, source):
        request = self.get_request("/en/")
        request.user = user
        # The admin sets ``_site``/``_request`` as class attributes via
        # ``get_form`` before instantiation (they are read in ``__init__``).
        form_cls = type(
            "TestDuplicatePageForm",
            (DuplicatePageForm,),
            {"_site": Site.objects.get_current(), "_request": request},
        )
        return form_cls(data={"source": source.pk, "title": "x", "slug": "x"})

    def test_duplicate_rejects_source_user_cannot_view(self):
        """A staff user with only 'add page' rights must not be able to copy a
        page they are not allowed to view (CWE-639 / CWE-862). ``source`` is a
        hidden, client-controlled field whose queryset spans every page.
        """
        superuser = self.get_superuser()
        secret = create_page("secret", "nav_playground.html", "en", created_by=superuser)
        # Add a view restriction so the page is only viewable by the superuser.
        self.add_page_permission(superuser, secret, can_view=True)

        attacker = self._create_user("attacker", is_staff=True, add_default_permissions=True)

        with self.settings(CMS_PERMISSION=True):
            form = self._build_form(attacker, secret)
            self.assertFalse(form.is_valid())
            self.assertIn("source", form.errors)

    def test_duplicate_allows_source_user_can_view(self):
        """Copying a page the user is allowed to view keeps working."""
        superuser = self.get_superuser()
        source = create_page("source", "nav_playground.html", "en", created_by=superuser)

        with self.settings(CMS_PERMISSION=True):
            form = self._build_form(superuser, source)
            # ``source`` must not be the reason the form is (in)valid.
            form.is_valid()
            self.assertNotIn("source", form.errors)


class ValidateUrlTestCase(CMSTestCase):
    """Regression tests for the dangerous-scheme bypass in ``validate_url``.

    ``relative_url_regex`` matches any value whose first segment contains no
    ``/<>``; a scheme such as ``javascript:`` was therefore accepted as a
    "relative URL" and never reached ``URLValidator``. Such schemes execute
    script when the value is later rendered into an ``href`` (CWE-79).
    """

    # Script-executing schemes -- these are the actual XSS vector.
    DANGEROUS = [
        "javascript:alert(1)/x",
        "JavaScript:alert(document.domain)/a",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)/x",
    ]

    VALID_RELATIVE = [
        "/foo/bar",
        "/foo/bar/",
        "foo/bar",
        "../page/",
        "./page/",
        "/en/some-slug/",
    ]

    VALID_ABSOLUTE = [
        "http://example.com/x",
        "https://example.com/x?y=1",
        # Protocol-relative / off-site targets navigate (not execute script)
        # and are an intended capability of this field; they must be accepted
        # just like an explicit ``https://`` URL.
        "//example.com",
        "//example.com/path",
    ]

    def test_dangerous_schemes_are_rejected(self):
        from cms.forms.validators import validate_url

        for value in self.DANGEROUS:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_url(value)

    def test_valid_relative_urls_are_accepted(self):
        from cms.forms.validators import validate_url

        for value in self.VALID_RELATIVE:
            with self.subTest(value=value):
                validate_url(value)  # must not raise

    def test_valid_absolute_urls_are_accepted(self):
        from cms.forms.validators import validate_url

        for value in self.VALID_ABSOLUTE:
            with self.subTest(value=value):
                validate_url(value)  # must not raise
