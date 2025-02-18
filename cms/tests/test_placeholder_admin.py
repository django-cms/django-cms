from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.forms.models import model_to_dict
from django.test.utils import CaptureQueriesContext, override_settings

from cms.api import add_plugin, create_page
from cms.models import CMSPlugin, Placeholder, UserSettings
from cms.test_utils.testcases import CMSTestCase
from cms.utils.urlutils import admin_reverse


class PlaceholderAdminTestCase(CMSTestCase):
    def test_add_plugin_endpoint(self):
        """
        The Placeholder admin add_plugin endpoint works
        """
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot="test")
        plugins = placeholder.get_plugins("en").filter(plugin_type="LinkPlugin")
        uri = self.get_add_plugin_uri(
            placeholder=placeholder,
            plugin_type="LinkPlugin",
            language="en",
        )
        with self.login_user_context(superuser):
            data = {"name": "A Link", "external_link": "https://www.django-cms.org"}
            response = self.client.post(uri, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(plugins.count(), 1)

    def test_add_plugin_with_ghost(self):
        """Adding a text plugin works. Text plugins create a ghost plugin."""
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot="test")
        plugins = placeholder.get_plugins("en").filter(plugin_type="TextPlugin")
        uri = self.get_add_plugin_uri(
            placeholder=placeholder,
            plugin_type="TextPlugin",
            language="en",
        )
        with self.login_user_context(superuser):
            data = {"body": "<p>Some markup</p>"}
            response = self.client.post(uri, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(plugins.count(), 1)

    def test_add_plugins_from_placeholder(self):
        """
        User can copy plugins from one placeholder to another
        """
        superuser = self.get_superuser()
        source_placeholder = Placeholder.objects.create(slot="source")
        target_placeholder = Placeholder.objects.create(slot="target")
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        endpoint = self.get_copy_plugin_uri(source_plugin)
        with self.login_user_context(superuser):
            data = {
                "source_language": "en",
                "source_placeholder_id": source_placeholder.pk,
                "target_language": "en",
                "target_placeholder_id": target_placeholder.pk,
            }
            response = self.client.post(endpoint, data)

        # Test that the target placeholder has the plugin copied from the source placeholder
        self.assertEqual(response.status_code, 200)
        self.assertTrue(source_placeholder.get_plugins("en").filter(pk=source_plugin.pk).exists())
        self.assertTrue(target_placeholder.get_plugins("en").filter(plugin_type=source_plugin.plugin_type).exists())

    def test_copy_plugins_to_clipboard(self):
        """
        User can copy plugins from a placeholder to the clipboard
        """
        superuser = self.get_superuser()
        user_settings = UserSettings.objects.create(
            language="en",
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )
        source_placeholder = Placeholder.objects.create(slot="source")
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        endpoint = self.get_copy_plugin_uri(source_plugin)
        with self.login_user_context(superuser):
            data = {
                "source_language": "en",
                "source_placeholder_id": source_placeholder.pk,
                "source_plugin_id": source_plugin.pk,
                "target_language": "en",
                "target_placeholder_id": user_settings.clipboard.pk,
            }
            response = self.client.post(endpoint, data)

        # Test that the target placeholder has the plugin copied from the source placeholder (clipboard)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(source_placeholder.get_plugins("en").filter(pk=source_plugin.pk).exists())
        self.assertTrue(
            user_settings.clipboard.get_plugins("en").filter(plugin_type=source_plugin.plugin_type).exists()
        )

    def test_copy_placeholder_to_clipboard(self):
        """
        User can copy a placeholder to the clipboard
        """
        superuser = self.get_superuser()
        user_settings = UserSettings.objects.create(
            language="en",
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )
        user_settings.clipboard.source = user_settings
        user_settings.clipboard.save()

        source_placeholder = Placeholder.objects.create(slot='source')
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        endpoint = self.get_copy_plugin_uri(source_plugin)
        with self.login_user_context(superuser):
            data = {
                "source_language": "en",
                "source_placeholder_id": source_placeholder.pk,
                "target_language": "en",
                "target_placeholder_id": user_settings.clipboard.pk,
            }
            response = self.client.post(endpoint, data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(source_placeholder.get_plugins("en").filter(pk=source_plugin.pk).exists())
        self.assertTrue(user_settings.clipboard.get_plugins("en").filter(plugin_type="PlaceholderPlugin").exists())

    def test_edit_plugin_endpoint(self):
        """
        The Placeholder admin edit_plugins endpoint works
        """
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot="edit_plugin_placeholder")
        plugin = self._add_plugin_to_placeholder(placeholder)
        endpoint = self.get_change_plugin_uri(plugin)
        with self.login_user_context(superuser):
            data = model_to_dict(plugin, fields=["name", "external_link"])
            data["name"] = "Contents modified"
            response = self.client.post(endpoint, data)
            plugin.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(plugin.name, data["name"])

    def test_delete_plugin_endpoint(self):
        """
        The Placeholder admin delete_plugin endpoint works
        """
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot="source")
        plugin = self._add_plugin_to_placeholder(placeholder)
        endpoint = self.get_delete_plugin_uri(plugin)
        with self.login_user_context(superuser):
            data = {"post": True}
            response = self.client.post(endpoint, data)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_clear_placeholder_endpoint(self):
        """
        The Placeholder admin delete_plugin endpoint works
        """
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot="source")
        self._add_plugin_to_placeholder(placeholder)
        endpoint = self.get_clear_placeholder_url(placeholder)
        with self.login_user_context(superuser):
            response = self.client.post(endpoint, {"test": 0})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(placeholder.get_plugins("en").count(), 0)

    def _fill_page_body(self, page, lang):
        ph_en = page.get_placeholders(lang).get(slot="placeholder")
        # add misc plugins
        mcol1 = add_plugin(ph_en, "MultiColumnPlugin", lang, position="first-child")
        add_plugin(ph_en, "ColumnPlugin", lang, position="first-child", target=mcol1)
        col2 = add_plugin(ph_en, "ColumnPlugin", lang, position="first-child", target=mcol1)
        mcol2 = add_plugin(ph_en, "MultiColumnPlugin", lang, position="first-child", target=col2)
        add_plugin(ph_en, "ColumnPlugin", lang, position="first-child", target=mcol2)
        col4 = add_plugin(ph_en, "ColumnPlugin", lang, position="first-child", target=mcol2)
        # add *nested* plugin without model
        add_plugin(ph_en, "NoCustomModel", lang, target=col4)
        # add *nested* link and text plugins
        add_plugin(ph_en, "LinkPlugin", lang, target=col4, name="A Link", external_link="https://www.django-cms.org")
        add_plugin(ph_en, "StylePlugin", lang, target=col4, tag_type="div")

    @override_settings(
        CMS_PLACEHOLDER_CONF={
            "simple.html": {"excluded_plugins": ["InheritPlugin"]},
        }
    )
    def test_object_edit_endpoint(self):
        page = create_page("Page 1", "simple.html", "en")
        self._fill_page_body(page, "en")
        content = page.get_content_obj()
        content_type = ContentType.objects.get(app_label="cms", model="pagecontent")
        user = self.get_superuser()
        settings = UserSettings.objects.create(
            language="en", user=user, clipboard=Placeholder.objects.create(slot="clipboard")
        )
        settings.clipboard.source = settings
        settings.clipboard.save()
        endpoint = admin_reverse(
            "cms_placeholder_render_object_edit",
            args=(
                content_type.pk,
                content.pk,
            ),
        )
        with self.login_user_context(user):
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(queries), 15, "\n".join([f"{i}. {q['sql']}" for i, q in enumerate(queries, start=1)]))
        # Queries
        # 1. SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user" WHERE "auth_user"."id" = 1 LIMIT 21
        # 2. SELECT "django_content_type"."id", "django_content_type"."app_label", "django_content_type"."model" FROM "django_content_type" WHERE "django_content_type"."id" = 18 LIMIT 21
        # 3. SELECT "cms_pagecontent"."id", "cms_pagecontent"."language", "cms_pagecontent"."title", "cms_pagecontent"."page_title", "cms_pagecontent"."menu_title", "cms_pagecontent"."meta_description", "cms_pagecontent"."redirect", "cms_pagecontent"."page_id", "cms_pagecontent"."creation_date", "cms_pagecontent"."created_by", "cms_pagecontent"."changed_by", "cms_pagecontent"."changed_date", "cms_pagecontent"."in_navigation", "cms_pagecontent"."soft_root", "cms_pagecontent"."template", "cms_pagecontent"."limit_visibility_in_menu", "cms_pagecontent"."xframe_options", "cms_page"."id", "cms_page"."path", "cms_page"."depth", "cms_page"."numchild", "cms_page"."parent_id", "cms_page"."site_id", "cms_page"."created_by", "cms_page"."changed_by", "cms_page"."creation_date", "cms_page"."changed_date", "cms_page"."reverse_id", "cms_page"."navigation_extenders", "cms_page"."login_required", "cms_page"."is_home", "cms_page"."application_urls", "cms_page"."application_namespace", "cms_page"."is_page_type" FROM "cms_pagecontent" INNER JOIN "cms_page" ON ("cms_pagecontent"."page_id" = "cms_page"."id") WHERE "cms_pagecontent"."id" = 1 LIMIT 21
        # 4. SELECT "cms_usersettings"."id", "cms_usersettings"."user_id", "cms_usersettings"."language", "cms_usersettings"."clipboard_id", "cms_placeholder"."id", "cms_placeholder"."slot", "cms_placeholder"."default_width", "cms_placeholder"."content_type_id", "cms_placeholder"."object_id" FROM "cms_usersettings" LEFT OUTER JOIN "cms_placeholder" ON ("cms_usersettings"."clipboard_id" = "cms_placeholder"."id") WHERE "cms_usersettings"."user_id" = 1 LIMIT 21
        # 5. SELECT "django_site"."id", "django_site"."domain", "django_site"."name" FROM "django_site" ORDER BY "django_site"."name" ASC
        # 6. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date", "cms_placeholder"."id", "cms_placeholder"."slot", "cms_placeholder"."default_width", "cms_placeholder"."content_type_id", "cms_placeholder"."object_id" FROM "cms_cmsplugin" INNER JOIN "cms_placeholder" ON ("cms_cmsplugin"."placeholder_id" = "cms_placeholder"."id") WHERE "cms_cmsplugin"."placeholder_id" = 2 ORDER BY "cms_cmsplugin"."position" ASC LIMIT 1
        # 7. SELECT 1 AS "a" FROM "cms_pagepermission" INNER JOIN "cms_page" ON ("cms_pagepermission"."page_id" = "cms_page"."id") WHERE (("cms_pagepermission"."page_id" = 1 AND ("cms_pagepermission"."grant_on" = 5 OR "cms_pagepermission"."grant_on" = 3 OR "cms_pagepermission"."grant_on" = 1)) AND "cms_pagepermission"."can_view") LIMIT 1
        # 8. SELECT "cms_pagecontent"."id", "cms_pagecontent"."language", "cms_pagecontent"."title", "cms_pagecontent"."page_title", "cms_pagecontent"."menu_title", "cms_pagecontent"."meta_description", "cms_pagecontent"."redirect", "cms_pagecontent"."page_id", "cms_pagecontent"."creation_date", "cms_pagecontent"."created_by", "cms_pagecontent"."changed_by", "cms_pagecontent"."changed_date", "cms_pagecontent"."in_navigation", "cms_pagecontent"."soft_root", "cms_pagecontent"."template", "cms_pagecontent"."limit_visibility_in_menu", "cms_pagecontent"."xframe_options" FROM "cms_pagecontent" WHERE "cms_pagecontent"."page_id" = 1
        # 9. SELECT "extensionapp_mypagecontentextension"."id", "extensionapp_mypagecontentextension"."public_extension_id", "extensionapp_mypagecontentextension"."extended_object_id", "extensionapp_mypagecontentextension"."extra_title" FROM "extensionapp_mypagecontentextension" WHERE "extensionapp_mypagecontentextension"."extended_object_id" = 1 LIMIT 21
        # 10. SELECT "extensionapp_mypageextension"."id", "extensionapp_mypageextension"."public_extension_id", "extensionapp_mypageextension"."extended_object_id", "extensionapp_mypageextension"."extra" FROM "extensionapp_mypageextension" WHERE "extensionapp_mypageextension"."extended_object_id" = 1 LIMIT 21
        # 11. SELECT "cms_placeholder"."id", "cms_placeholder"."slot", "cms_placeholder"."default_width", "cms_placeholder"."content_type_id", "cms_placeholder"."object_id" FROM "cms_placeholder" WHERE ("cms_placeholder"."content_type_id" = 18 AND "cms_placeholder"."object_id" = 1)
        # 12. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date" FROM "cms_cmsplugin" WHERE ("cms_cmsplugin"."language" = 'en' AND "cms_cmsplugin"."placeholder_id" IN (1)) ORDER BY "cms_cmsplugin"."position" ASC
        # 13. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date", "multicolumn_multicolumns"."cmsplugin_ptr_id" FROM "multicolumn_multicolumns" INNER JOIN "cms_cmsplugin" ON ("multicolumn_multicolumns"."cmsplugin_ptr_id" = "cms_cmsplugin"."id") WHERE "multicolumn_multicolumns"."cmsplugin_ptr_id" IN (1, 4) ORDER BY "cms_cmsplugin"."position" ASC
        # 14. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date", "link_link"."cmsplugin_ptr_id", "link_link"."name", "link_link"."external_link" FROM "link_link" INNER JOIN "cms_cmsplugin" ON ("link_link"."cmsplugin_ptr_id" = "cms_cmsplugin"."id") WHERE "link_link"."cmsplugin_ptr_id" IN (7) ORDER BY "cms_cmsplugin"."position" ASC
        # 15. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date", "style_style"."cmsplugin_ptr_id", "style_style"."label", "style_style"."tag_type", "style_style"."class_name", "style_style"."additional_classes" FROM "style_style" INNER JOIN "cms_cmsplugin" ON ("style_style"."cmsplugin_ptr_id" = "cms_cmsplugin"."id") WHERE "style_style"."cmsplugin_ptr_id" IN (9) ORDER BY "cms_cmsplugin"."position" ASC

    @override_settings(
        CMS_PLACEHOLDER_CONF={
            "simple.html": {"excluded_plugins": ["InheritPlugin"]},
        }
    )
    def test_object_structure_endpoint(self):
        page = create_page("Page 1", "simple.html", "en")
        self._fill_page_body(page, "en")
        content = page.get_content_obj()
        content_type = ContentType.objects.get(app_label="cms", model="pagecontent")
        user = self.get_superuser()
        settings = UserSettings.objects.create(
            language="en", user=user, clipboard=Placeholder.objects.create(slot="clipboard")
        )
        settings.clipboard.source = settings
        settings.clipboard.save()

        endpoint = admin_reverse(
            "cms_placeholder_render_object_structure",
            args=(
                content_type.pk,
                content.pk,
            ),
        )
        with self.login_user_context(user):
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(queries), 17, "\n".join([f"{i}. {q['sql']}" for i, q in enumerate(queries, start=1)]))
        # Queries
        # 1. SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user" WHERE "auth_user"."id" = 1 LIMIT 21
        # 2. SELECT "django_content_type"."id", "django_content_type"."app_label", "django_content_type"."model" FROM "django_content_type" WHERE "django_content_type"."id" = 18 LIMIT 21
        # 3. SELECT "cms_pagecontent"."id", "cms_pagecontent"."language", "cms_pagecontent"."title", "cms_pagecontent"."page_title", "cms_pagecontent"."menu_title", "cms_pagecontent"."meta_description", "cms_pagecontent"."redirect", "cms_pagecontent"."page_id", "cms_pagecontent"."creation_date", "cms_pagecontent"."created_by", "cms_pagecontent"."changed_by", "cms_pagecontent"."changed_date", "cms_pagecontent"."in_navigation", "cms_pagecontent"."soft_root", "cms_pagecontent"."template", "cms_pagecontent"."limit_visibility_in_menu", "cms_pagecontent"."xframe_options", "cms_page"."id", "cms_page"."path", "cms_page"."depth", "cms_page"."numchild", "cms_page"."parent_id", "cms_page"."site_id", "cms_page"."created_by", "cms_page"."changed_by", "cms_page"."creation_date", "cms_page"."changed_date", "cms_page"."reverse_id", "cms_page"."navigation_extenders", "cms_page"."login_required", "cms_page"."is_home", "cms_page"."application_urls", "cms_page"."application_namespace", "cms_page"."is_page_type" FROM "cms_pagecontent" INNER JOIN "cms_page" ON ("cms_pagecontent"."page_id" = "cms_page"."id") WHERE "cms_pagecontent"."id" = 1 LIMIT 21
        # 4. SELECT "cms_usersettings"."id", "cms_usersettings"."user_id", "cms_usersettings"."language", "cms_usersettings"."clipboard_id", "cms_placeholder"."id", "cms_placeholder"."slot", "cms_placeholder"."default_width", "cms_placeholder"."content_type_id", "cms_placeholder"."object_id" FROM "cms_usersettings" LEFT OUTER JOIN "cms_placeholder" ON ("cms_usersettings"."clipboard_id" = "cms_placeholder"."id") WHERE "cms_usersettings"."user_id" = 1 LIMIT 21
        # 5. SELECT "cms_pagecontent"."id", "cms_pagecontent"."language", "cms_pagecontent"."title", "cms_pagecontent"."page_title", "cms_pagecontent"."menu_title", "cms_pagecontent"."meta_description", "cms_pagecontent"."redirect", "cms_pagecontent"."page_id", "cms_pagecontent"."creation_date", "cms_pagecontent"."created_by", "cms_pagecontent"."changed_by", "cms_pagecontent"."changed_date", "cms_pagecontent"."in_navigation", "cms_pagecontent"."soft_root", "cms_pagecontent"."template", "cms_pagecontent"."limit_visibility_in_menu", "cms_pagecontent"."xframe_options" FROM "cms_pagecontent" WHERE "cms_pagecontent"."page_id" = 1
        # 6. SELECT "django_site"."id", "django_site"."domain", "django_site"."name" FROM "django_site" ORDER BY "django_site"."name" ASC
        # 7. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date", "cms_placeholder"."id", "cms_placeholder"."slot", "cms_placeholder"."default_width", "cms_placeholder"."content_type_id", "cms_placeholder"."object_id" FROM "cms_cmsplugin" INNER JOIN "cms_placeholder" ON ("cms_cmsplugin"."placeholder_id" = "cms_placeholder"."id") WHERE "cms_cmsplugin"."placeholder_id" = 2 ORDER BY "cms_cmsplugin"."position" ASC LIMIT 1
        # 8. SELECT 1 AS "a" FROM "cms_pagepermission" INNER JOIN "cms_page" ON ("cms_pagepermission"."page_id" = "cms_page"."id") WHERE (("cms_pagepermission"."page_id" = 1 AND ("cms_pagepermission"."grant_on" = 5 OR "cms_pagepermission"."grant_on" = 3 OR "cms_pagepermission"."grant_on" = 1)) AND "cms_pagepermission"."can_view") LIMIT 1
        # 9. SELECT "cms_pagecontent"."id", "cms_pagecontent"."language", "cms_pagecontent"."title", "cms_pagecontent"."page_title", "cms_pagecontent"."menu_title", "cms_pagecontent"."meta_description", "cms_pagecontent"."redirect", "cms_pagecontent"."page_id", "cms_pagecontent"."creation_date", "cms_pagecontent"."created_by", "cms_pagecontent"."changed_by", "cms_pagecontent"."changed_date", "cms_pagecontent"."in_navigation", "cms_pagecontent"."soft_root", "cms_pagecontent"."template", "cms_pagecontent"."limit_visibility_in_menu", "cms_pagecontent"."xframe_options" FROM "cms_pagecontent" WHERE "cms_pagecontent"."page_id" = 1
        # 10. SELECT "extensionapp_mypagecontentextension"."id", "extensionapp_mypagecontentextension"."public_extension_id", "extensionapp_mypagecontentextension"."extended_object_id", "extensionapp_mypagecontentextension"."extra_title" FROM "extensionapp_mypagecontentextension" WHERE "extensionapp_mypagecontentextension"."extended_object_id" = 1 LIMIT 21
        # 11. SELECT "extensionapp_mypageextension"."id", "extensionapp_mypageextension"."public_extension_id", "extensionapp_mypageextension"."extended_object_id", "extensionapp_mypageextension"."extra" FROM "extensionapp_mypageextension" WHERE "extensionapp_mypageextension"."extended_object_id" = 1 LIMIT 21
        # 12. SELECT "cms_placeholder"."id", "cms_placeholder"."slot", "cms_placeholder"."default_width", "cms_placeholder"."content_type_id", "cms_placeholder"."object_id" FROM "cms_placeholder" WHERE ("cms_placeholder"."content_type_id" = 18 AND "cms_placeholder"."object_id" = 1)
        # 13. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date" FROM "cms_cmsplugin" WHERE ("cms_cmsplugin"."language" = 'en' AND "cms_cmsplugin"."placeholder_id" IN (1)) ORDER BY "cms_cmsplugin"."position" ASC
        # 14. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date", "multicolumn_multicolumns"."cmsplugin_ptr_id" FROM "multicolumn_multicolumns" INNER JOIN "cms_cmsplugin" ON ("multicolumn_multicolumns"."cmsplugin_ptr_id" = "cms_cmsplugin"."id") WHERE "multicolumn_multicolumns"."cmsplugin_ptr_id" IN (1, 4) ORDER BY "cms_cmsplugin"."position" ASC
        # 15. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date", "link_link"."cmsplugin_ptr_id", "link_link"."name", "link_link"."external_link" FROM "link_link" INNER JOIN "cms_cmsplugin" ON ("link_link"."cmsplugin_ptr_id" = "cms_cmsplugin"."id") WHERE "link_link"."cmsplugin_ptr_id" IN (7) ORDER BY "cms_cmsplugin"."position" ASC
        # 16. SELECT "cms_cmsplugin"."language" AS "language" FROM "cms_cmsplugin" WHERE "cms_cmsplugin"."placeholder_id" = 1 ORDER BY "cms_cmsplugin"."position" ASC
        # 17. SELECT "cms_cmsplugin"."id", "cms_cmsplugin"."placeholder_id", "cms_cmsplugin"."parent_id", "cms_cmsplugin"."position", "cms_cmsplugin"."language", "cms_cmsplugin"."plugin_type", "cms_cmsplugin"."creation_date", "cms_cmsplugin"."changed_date", "style_style"."cmsplugin_ptr_id", "style_style"."label", "style_style"."tag_type", "style_style"."class_name", "style_style"."additional_classes" FROM "style_style" INNER JOIN "cms_cmsplugin" ON ("style_style"."cmsplugin_ptr_id" = "cms_cmsplugin"."id") WHERE "style_style"."cmsplugin_ptr_id" IN (9) ORDER BY "cms_cmsplugin"."position" ASC

    def test_get_toolbar_endpoint(self):
        """Toolbar endpoint returns the toolbar including the page menu when called from the edit endpoint"""
        page = create_page("Page 1", "simple.html", "en")
        self._fill_page_body(page, "en")
        content = page.get_content_obj()
        content_type = ContentType.objects.get(app_label="cms", model="pagecontent")
        user = self.get_superuser()
        toolbar_endpoint = admin_reverse("cms_usersettings_get_toolbar")
        edit_endpoint = admin_reverse(
            "cms_placeholder_render_object_edit",
            args=(
                content_type.pk,
                content.pk,
            ),
        )

        with self.login_user_context(user):
            response = self.client.get(f"{toolbar_endpoint}?obj_id={content.id}&obj_type=cms.pagecontent&cms_path={edit_endpoint}")

        self.assertContains(response, '<span>Page<span class="cms-icon cms-icon-arrow"></span></span>')  # Contains page menu
