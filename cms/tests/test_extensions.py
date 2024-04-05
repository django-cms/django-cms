from copy import deepcopy

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site

from cms.api import create_page, create_page_content
from cms.extensions import PageContentExtension, PageExtension, extension_pool
from cms.extensions.toolbar import ExtensionToolbar
from cms.models import Page, PageContent
from cms.test_utils.project.extensionapp.models import (
    MultiTablePageContentExtension,
    MultiTablePageExtension,
    MyPageContentExtension,
    MyPageExtension,
)
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar_pool import toolbar_pool
from cms.utils.compat.warnings import RemovedInDjangoCMS42Warning, RemovedInDjangoCMS43Warning
from cms.utils.urlutils import admin_reverse


class ExtensionsTestCase(CMSTestCase):
    def test_register_extension(self):
        initial_extension_count = len(extension_pool.page_extensions)
        # --- None extension registering -----------------------------
        from cms.exceptions import SubClassNeededError
        none_extension = self.get_none_extension_class()
        self.assertRaises(SubClassNeededError, extension_pool.register, none_extension)
        self.assertEqual(len(extension_pool.page_extensions), initial_extension_count)
        self.assertEqual(len(extension_pool.page_content_extensions), initial_extension_count)

        # --- Page registering ---------------------------------------
        page_extension = self.get_page_extension_class()

        # register first time
        extension_pool.register(page_extension)
        self.assertEqual(len(extension_pool.page_extensions), initial_extension_count + 1)

        # register second time
        extension_pool.register(page_extension)
        self.assertEqual(len(extension_pool.page_extensions), initial_extension_count + 1)

        # --- Page Content registering -------------------------------
        page_content_extension = self.get_page_content_extension_class()

        # register first time
        extension_pool.register(page_content_extension)
        self.assertEqual(len(extension_pool.page_content_extensions), initial_extension_count + 1)

        # register second time
        extension_pool.register(page_content_extension)
        self.assertEqual(len(extension_pool.page_content_extensions), initial_extension_count + 1)

        # --- Unregister ---------------------------------------------
        extension_pool.unregister(page_extension)
        self.assertEqual(len(extension_pool.page_extensions), initial_extension_count)

        extension_pool.unregister(page_content_extension)
        self.assertEqual(len(extension_pool.page_content_extensions), initial_extension_count)

        # Unregister an object that is not registered yet
        extension_pool.unregister(page_extension)
        extension_pool.unregister(page_content_extension)

    def get_page_extension_class(self):
        from django.db import models

        class TestPageExtension(PageExtension):
            content = models.CharField('Content', max_length=50)

            class Meta:
                abstract = True

        return TestPageExtension

    def get_page_content_extension_class(self):
        from django.db import models

        class TestPageContentExtension(PageContentExtension):
            content = models.CharField('Content', max_length=50)

            class Meta:
                abstract = True

        return TestPageContentExtension

    def get_none_extension_class(self):
        class TestNoneExtension:
            pass

        return TestNoneExtension

    def test_copy_extensions(self):
        root = create_page('Root', "nav_playground.html", "en")
        page = create_page('Test Page Extension', "nav_playground.html", "en", parent=root)
        subpage = create_page('Test subpage Extension', "nav_playground.html", "en", parent=page)
        page = Page.objects.get(pk=page.pk)
        page_extension = MyPageExtension(extended_object=page, extra='page extension 1')
        page_extension.save()
        page.mypageextension = page_extension
        page_content = page.get_content_obj()
        page_content_extension = MyPageContentExtension(extended_object=page_content, extra_title='title extension 1')
        page_content_extension.save()
        page.myPageContentExtension = page_content_extension

        subpage_extension = MyPageExtension(extended_object=subpage, extra='page extension 2')
        subpage_extension.save()
        subpage.mypageextension = subpage_extension
        subpage_content = subpage.get_content_obj()
        subpage_content_extension = MyPageContentExtension(
            extended_object=subpage_content,
            extra_title='title extension 2'
        )
        subpage_content_extension.save()
        subpage.myPageContentExtension = subpage_content_extension

        # asserting original extensions
        self.assertEqual(len(extension_pool.get_page_extensions()), 2)
        self.assertEqual(len(extension_pool.get_page_content_extensions()), 2)
        copied_page = page.copy_with_descendants(target_node=None, position='last-child', user=self.get_superuser())

        # asserting original + copied extensions
        self.assertEqual(len(extension_pool.get_page_extensions()), 4)
        self.assertEqual(len(extension_pool.get_page_content_extensions()), 4)

        # testing extension content
        old_page_extensions = [page_extension, subpage_extension]
        old_title_extension = [page_content_extension, subpage_content_extension]
        for index, new_page in enumerate([copied_page] + list(copied_page.get_descendant_pages())):
            self.assertEqual(
                extension_pool.get_page_extensions(new_page)[0].extra,
                old_page_extensions[index].extra
            )
            self.assertEqual(
                extension_pool.get_page_content_extensions(
                    new_page.pagecontent_set.get(language='en')
                )[0].extra_title,
                old_title_extension[index].extra_title
            )
            # check that objects are actually different
            self.assertNotEqual(
                extension_pool.get_page_extensions(new_page)[0].pk,
                old_page_extensions[index].pk
            )
            self.assertNotEqual(
                extension_pool.get_page_content_extensions(new_page.pagecontent_set.get(language='en'))[0].pk,
                old_title_extension[index].pk
            )

        # Test deleting original page for #3987
        page.delete()
        # asserting original extensions are gone, but copied ones should still exist
        self.assertEqual(len(extension_pool.get_page_extensions()), 2)
        self.assertEqual(len(extension_pool.get_page_content_extensions()), 2)

    def test_copy_multitable_extensions(self):
        root = create_page('Root', "nav_playground.html", "en")
        page = create_page('Test Multi-Table Page Extension', "nav_playground.html", "en", parent=root)
        subpage = create_page('Test Multi-Table subpage Extension', "nav_playground.html", "en", parent=page)
        page = Page.objects.get(pk=page.pk)
        page_extension = MultiTablePageExtension(
            extended_object=page,
            extension_parent_field='page extension 1',
            multitable_extra='multi-table page extension 1'
        )
        page_extension.save()
        page.multitablepageextension = page_extension
        title = page.get_content_obj()
        title_extension = MultiTablePageContentExtension(
            extended_object=title,
            extension_content_parent_field='content extension 1',
            multitable_extra_content='multi-table content extension 1'
        )
        title_extension.save()
        page.multitablepagecontentextension = title_extension

        subpage_extension = MultiTablePageExtension(
            extended_object=subpage,
            extension_parent_field='page extension 2',
            multitable_extra='multi-table page extension 2'
        )
        subpage_extension.save()
        subpage.multitablepageextension = subpage_extension
        subtitle = subpage.get_content_obj()
        subtitle_extension = MultiTablePageContentExtension(
            extended_object=subtitle,
            extension_content_parent_field='title extension 2',
            multitable_extra_content='multi-table title extension 2'
        )
        subtitle_extension.save()
        subpage.multitablepagecontentextension = subtitle_extension

        # asserting original extensions
        self.assertEqual(len(extension_pool.get_page_extensions()), 2)
        self.assertEqual(len(extension_pool.get_page_content_extensions()), 2)

        copied_page = page.copy_with_descendants(target_node=None, position='last-child', user=self.get_superuser())

        # asserting original + copied extensions
        self.assertEqual(len(extension_pool.get_page_extensions()), 4)
        self.assertEqual(len(extension_pool.get_page_content_extensions()), 4)

        # testing extension content
        old_page_extensions = [page_extension, subpage_extension]
        old_title_extension = [title_extension, subtitle_extension]
        for index, new_page in enumerate([copied_page] + list(copied_page.get_descendant_pages())):
            copied_page_extension = extension_pool.get_page_extensions(new_page)[0]
            copied_title_extension = extension_pool.get_page_content_extensions(
                new_page.pagecontent_set.get(language='en')
            )[0]
            self.assertEqual(
                copied_page_extension.extension_parent_field,
                old_page_extensions[index].extension_parent_field
            )
            self.assertEqual(
                copied_page_extension.multitable_extra,
                old_page_extensions[index].multitable_extra
            )
            self.assertEqual(
                copied_title_extension.extension_content_parent_field,
                old_title_extension[index].extension_content_parent_field
            )
            self.assertEqual(
                copied_title_extension.multitable_extra_content,
                old_title_extension[index].multitable_extra_content
            )
            # check that objects are actually different
            self.assertNotEqual(
                extension_pool.get_page_extensions(new_page)[0].pk,
                old_page_extensions[index].pk
            )
            self.assertNotEqual(
                extension_pool.get_page_content_extensions(new_page.pagecontent_set.get(language='en'))[0].pk,
                old_title_extension[index].pk
            )

        # Test deleting original page for #3987
        page.delete()
        # asserting original extensions are gone, but copied ones should still exist
        self.assertEqual(len(extension_pool.get_page_extensions()), 2)
        self.assertEqual(len(extension_pool.get_page_content_extensions()), 2)


class ExtensionAdminTestCase(CMSTestCase):

    def setUp(self):
        User = get_user_model()

        self.admin = self.get_superuser()
        self.normal_guy = self.get_staff_user_with_std_permissions()

        if get_user_model().USERNAME_FIELD == 'email':
            self.no_page_permission_user = User.objects.create_user(
                'no_page_permission', 'test2@test.com', 'test2@test.com'
            )
        else:
            self.no_page_permission_user = User.objects.create_user(
                'no_page_permission', 'test2@test.com', 'no_page_permission'
            )

        self.no_page_permission_user.is_staff = True
        self.no_page_permission_user.is_active = True
        self.no_page_permission_user.save()
        [self.no_page_permission_user.user_permissions.add(p) for p in Permission.objects.filter(
            codename__in=[
                'change_mypageextension', 'change_myPageContentExtension',
                'add_mypageextension', 'add_myPageContentExtension',
                'delete_mypageextension', 'delete_myPageContentExtension',
            ]
        )]
        self.site = Site.objects.get(pk=1)
        self.page = create_page(
            'My Extension Page', 'nav_playground.html', 'en',
            site=self.site, created_by=self.admin)
        self.page_title = self.page.get_content_obj('en')
        create_page_content('de', 'de title', self.page)
        self.page_extension = MyPageExtension.objects.create(
            extended_object=self.page,
            extra="page extension text")
        self.title_extension = MyPageContentExtension.objects.create(
            extended_object=self.page.get_content_obj(),
            extra_title="title extension text")

        self.page_without_extension = create_page(
            'A Page', 'nav_playground.html', 'en',
            site=self.site, created_by=self.admin)
        self.page_title_without_extension = self.page_without_extension.get_content_obj()

    def test_duplicate_extensions(self):
        with self.login_user_context(self.admin):
            content = self.get_pagecontent_obj(self.page, 'en')
            # create page copy
            page_data = {
                'title': 'type1', 'slug': 'type1', '_save': 1, 'template': 'nav_playground.html',
                'site': 1, 'language': 'en', 'source': self.page.pk,
            }
            self.assertEqual(Page.objects.all().count(), 2)
            self.assertEqual(MyPageExtension.objects.all().count(), 1)
            self.assertEqual(MyPageContentExtension.objects.all().count(), 1)
            response = self.client.post(
                self.get_admin_url(PageContent, 'duplicate', content.pk),
                data=page_data,
            )
            # Check that page and its extensions have been copied
            self.assertRedirects(response, self.get_pages_admin_list_uri('en'))
            self.assertEqual(Page.objects.all().count(), 3)
            self.assertEqual(MyPageExtension.objects.all().count(), 2)
            self.assertEqual(MyPageContentExtension.objects.all().count(), 2)

    def test_admin_page_extension(self):
        with self.login_user_context(self.admin):
            # add a new extension
            response = self.client.get(
                admin_reverse(
                    'extensionapp_mypageextension_add'
                ) + '?extended_object=%s' % self.page_without_extension.pk
            )
            self.assertEqual(response.status_code, 200)
            # make sure there is no extension yet
            self.assertFalse(MyPageExtension.objects.filter(extended_object=self.page_without_extension).exists())
            post_data = {
                'extra': 'my extra'
            }
            response = self.client.post(
                admin_reverse(
                    'extensionapp_mypageextension_add'
                ) + '?extended_object=%s' % self.page_without_extension.pk,
                post_data, follow=True
            )
            created_page_extension = MyPageExtension.objects.get(extended_object=self.page_without_extension)

            # can delete extension
            response = self.client.post(
                admin_reverse('extensionapp_mypageextension_delete', args=(created_page_extension.pk,)),
                {'post': 'yes'}, follow=True
            )
            self.assertFalse(MyPageExtension.objects.filter(extended_object=self.page_without_extension).exists())

            # accessing the add view on a page that already has an extension should redirect
            response = self.client.get(
                admin_reverse('extensionapp_mypageextension_add') + '?extended_object=%s' % self.page.pk
            )
            self.assertRedirects(
                response, admin_reverse('extensionapp_mypageextension_change', args=(self.page_extension.pk,))
            )

            # saving an extension should work without the GET parameter
            post_data = {
                'extra': 'my extra text'
            }
            self.client.post(
                admin_reverse('extensionapp_mypageextension_change', args=(self.page_extension.pk,)),
                post_data, follow=True
            )
            self.assertTrue(MyPageExtension.objects.filter(extra='my extra text', pk=self.page_extension.pk).exists())

        with self.login_user_context(self.no_page_permission_user):
            # can't save if user does not have permissions to change the page
            post_data = {
                'extra': 'try to change extra text'
            }
            response = self.client.post(
                admin_reverse('extensionapp_mypageextension_change', args=(self.page_extension.pk,)),
                post_data, follow=True
            )
            self.assertEqual(response.status_code, 403)

            # can't delete without page permission
            response = self.client.post(
                admin_reverse('extensionapp_mypageextension_delete', args=(self.page_extension.pk,)),
                {'post': 'yes'}, follow=True
            )
            self.assertEqual(response.status_code, 403)
            self.assertTrue(MyPageExtension.objects.filter(extended_object=self.page).exists())

    def test_toolbar_page_extension(self):
        old_toolbars = deepcopy(toolbar_pool.toolbars)

        class SampleExtension(ExtensionToolbar):
            model = MyPageExtension  # The PageExtension / TitleExtension you are working with

            def populate(self):
                current_page_menu = self._setup_extension_toolbar()
                if current_page_menu:
                    position = 0
                    page_extension, url = self.get_page_extension_admin()
                    if url:
                        current_page_menu.add_modal_item(
                            'TestItem',
                            url=url,
                            disabled=not self.toolbar.edit_mode_active,
                            position=position
                        )
        toolbar_pool.register(SampleExtension)
        with self.login_user_context(self.admin):
            response = self.client.get(f'{self.page.get_absolute_url()}?edit')
            self.assertIn("TestItem", response.rendered_content)
        toolbar_pool.toolbars = old_toolbars

    def test_toolbar_page_content_extension(self):
        old_toolbars = deepcopy(toolbar_pool.toolbars)

        class SampleExtension(ExtensionToolbar):
            model = MyPageContentExtension

            def populate(self):
                current_page_menu = self._setup_extension_toolbar()
                if current_page_menu:
                    position = 0
                    pagecontent_extension, url = self.get_page_content_extension_admin()
                    current_page_menu.add_modal_item(
                        'TestItem',
                        url=url,
                        disabled=not self.toolbar.edit_mode_active,
                        position=position
                    )
        toolbar_pool.register(SampleExtension)
        with self.login_user_context(self.admin):
            response = self.client.get(f'{self.page.get_absolute_url()}?edit')
            self.assertIn("TestItem", response.rendered_content)
        toolbar_pool.toolbars = old_toolbars

    def test_deprecated_title_extension(self):
        urls = []
        old_toolbars = deepcopy(toolbar_pool.toolbars)

        class SampleExtensionToolbar2(ExtensionToolbar):
            model = MyPageContentExtension
            def populate(self):
                nonlocal urls
                urls = self.get_title_extension_admin()

        toolbar_pool.register(SampleExtensionToolbar2)

        message = "get_title_extension_admin has been deprecated and replaced by get_page_content_extension_admin"
        with self.login_user_context(self.admin):
            self.assertWarns(
                RemovedInDjangoCMS43Warning,
                message,
                lambda: self.client.get(self.page.get_absolute_url()),
            )

        self.assertEqual(len(urls), 2)
        toolbar_pool.toolbars = old_toolbars

    def test_admin_title_extension(self):
        with self.login_user_context(self.admin):
            # add a new extension
            response = self.client.get(
                admin_reverse(
                    'extensionapp_mypagecontentextension_add'
                ) + '?extended_object=%s' % self.page_title_without_extension.pk
            )
            self.assertEqual(response.status_code, 200)
            # make sure there is no extension yet
            self.assertFalse(
                MyPageContentExtension.objects.filter(extended_object=self.page_title_without_extension).exists()
            )
            post_data = {
                'extra_title': 'my extra title'
            }
            self.client.post(
                admin_reverse(
                    'extensionapp_mypagecontentextension_add'
                ) + '?extended_object=%s' % self.page_title_without_extension.pk,
                post_data, follow=True
            )
            created_title_extension = MyPageContentExtension.objects.get(
                extended_object=self.page_title_without_extension
            )

            # can delete extension
            self.client.post(
                admin_reverse('extensionapp_mypagecontentextension_delete', args=(created_title_extension.pk,)),
                {'post': 'yes'}, follow=True
            )
            self.assertFalse(
                MyPageContentExtension.objects.filter(extended_object=self.page_title_without_extension).exists()
            )

            # accessing the add view on a page that already has an extension should redirect
            response = self.client.get(
                admin_reverse('extensionapp_mypagecontentextension_add') + '?extended_object=%s' % self.page_title.pk
            )
            self.assertRedirects(
                response, admin_reverse('extensionapp_mypagecontentextension_change', args=(self.title_extension.pk,))
            )

            # saving an extension should work without the GET parameter
            post_data = {
                'extra_title': 'my extra text'
            }
            self.client.post(
                admin_reverse('extensionapp_mypagecontentextension_change', args=(self.title_extension.pk,)),
                post_data, follow=True
            )
            self.assertTrue(
                MyPageContentExtension.objects.filter(extra_title='my extra text', pk=self.title_extension.pk).exists()
            )

        with self.login_user_context(self.no_page_permission_user):
            # can't save if user does not have permissions to change the page
            post_data = {
                'extra_title': 'try to change extra text'
            }
            response = self.client.post(
                admin_reverse('extensionapp_mypagecontentextension_change', args=(self.title_extension.pk,)),
                post_data, follow=True
            )
            self.assertEqual(response.status_code, 403)

            # can't delete without page permission
            response = self.client.post(
                admin_reverse('extensionapp_mypagecontentextension_delete', args=(self.title_extension.pk,)),
                {'post': 'yes'}, follow=True
            )
            self.assertEqual(response.status_code, 403)
            self.assertTrue(MyPageContentExtension.objects.filter(extended_object=self.page_title).exists())
