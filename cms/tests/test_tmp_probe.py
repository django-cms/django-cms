import json

from django.contrib.auth.models import Permission
from django.test.utils import override_settings

from cms.api import assign_user_to_page, create_page
from cms.models import Placeholder, UserSettings
from cms.test_utils.testcases import CMSTestCase
from cms.utils import page_permissions
from cms.utils.urlutils import admin_reverse


@override_settings(CMS_PERMISSION=True)
class ProbeTreeVsAutocomplete(CMSTestCase):
    def _low_priv_user(self):
        user = self._create_user("lowpriv", is_staff=True, is_superuser=False)
        # Only grant what is needed to reach the admin gateway: change_page
        # (required by the gateway helper) + pagecontent admin access.
        # Deliberately NOT granting view_page (that grants view-all).
        for codename in ("change_page", "change_pagecontent", "view_pagecontent"):
            for perm in Permission.objects.filter(codename=codename):
                user.user_permissions.add(perm)
        return user

    def test_probe(self):
        public = create_page("PublicHome", "nav_playground.html", "en", slug="public-home")
        secret = create_page("SecretRestricted", "nav_playground.html", "en", slug="secret-restricted")

        # Make `secret` view-restricted, granted to a DIFFERENT user.
        other = self._create_user("other", is_staff=True, is_superuser=False)
        assign_user_to_page(secret, other, can_view=True)

        user = self._low_priv_user()
        # low-priv can change ONLY the public page (no rights on secret)
        assign_user_to_page(public, user, can_change=True)

        print("\n=== restrictions ===")
        print("public restricted?", public.has_view_restrictions(public.site))
        print("secret restricted?", secret.has_view_restrictions(secret.site))

        print("\n=== user_can_view_page (low priv) ===")
        print("public:", page_permissions.user_can_view_page(user, public, public.site))
        print("secret:", page_permissions.user_can_view_page(user, secret, secret.site))
        print("=== user_can_change_page (low priv) ===")
        print("public:", page_permissions.user_can_change_page(user, public, public.site))
        print("secret:", page_permissions.user_can_change_page(user, secret, secret.site))

        # 1) Autocomplete endpoint
        endpoint = admin_reverse("cms_page_get_list")
        with self.login_user_context(user):
            resp = self.client.get(
                endpoint,
                data={"site": public.site_id, "q": "", "language_code": "en"},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        autocomplete_titles = {r["title"] for r in json.loads(resp.content.decode())}
        print("\n=== AUTOCOMPLETE titles (low priv) ===", autocomplete_titles)

        # 2) Page tree endpoint
        UserSettings.objects.get_or_create(
            user=user,
            defaults={"language": "en", "clipboard": Placeholder.objects.create(slot="clipboard")},
        )
        tree_endpoint = admin_reverse("cms_pagecontent_get_tree")
        with self.login_user_context(user):
            tresp = self.client.get(tree_endpoint, data={"language": "en"})
        tree_html = tresp.content.decode()
        print("\n=== PAGE TREE (low priv) === status:", tresp.status_code)
        print("PublicHome in tree:", "PublicHome" in tree_html)
        print("SecretRestricted in tree:", "SecretRestricted" in tree_html)
