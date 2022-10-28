from copy import deepcopy

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site

from cms.api import create_page, create_title
from cms.constants import PUBLISHER_STATE_DIRTY
from cms.extensions import PageExtension, TitleExtension, extension_pool
from cms.extensions.toolbar import ExtensionToolbar
from cms.models import Page, PageType
from cms.test_utils.project.extensionapp.models import (
    MultiTablePageExtension, MultiTableTitleExtension, MyPageExtension, MyTitleExtension,
)
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar_pool import toolbar_pool
from cms.utils.urlutils import admin_reverse


class ExtensionsTestCase(CMSTestCase):
    def test_register_extension(self):
        initial_extension_count = len(extension_pool.page_extensions)
        # --- None extension registering -----------------------------
        from cms.exceptions import SubClassNeededError
        none_extension = self.get_none_extension_class()
        self.assertRaises(SubClassNeededError, extension_pool.register, none_extension)
        self.assertEqual(len(extension_pool.page_extensions), initial_extension_count)
        self.assertEqual(len(extension_pool.title_extensions), initial_extension_count)

        # --- Page registering ---------------------------------------
        page_extension = self.get_page_extension_class()

        # register first time
        extension_pool.register(page_extension)
        self.assertEqual(len(extension_pool.page_extensions), initial_extension_count+1)

        # register second time
        extension_pool.register(page_extension)
        self.assertEqual(len(extension_pool.page_extensions), initial_extension_count+1)

        self.assertIs(extension_pool.signaling_activated, True)

        # --- Title registering --------------------------------------
        title_extension = self.get_title_extension_class()

        # register first time
        extension_pool.register(title_extension)
        self.assertEqual(len(extension_pool.title_extensions), initial_extension_count+1)

        # register second time
        extension_pool.register(title_extension)
        self.assertEqual(len(extension_pool.title_extensions), initial_extension_count+1)

        self.assertIs(extension_pool.signaling_activated, True)

        # --- Unregister ---------------------------------------------
        extension_pool.unregister(page_extension)
        self.assertEqual(len(extension_pool.page_extensions), initial_extension_count)

        extension_pool.unregister(title_extension)
        self.assertEqual(len(extension_pool.title_extensions), initial_extension_count)

        # Unregister an object that is not registered yet
        extension_pool.unregister(page_extension)
        extension_pool.unregister(title_extension)

    @staticmethod
    def get_page_extension_class():
        from django.db import models

        class TestPageExtension(PageExtension):
            content = models.CharField('Content', max_length=50)

            class Meta:
                abstract = True

        return TestPageExtension

    @staticmethod
    def get_title_extension_class():
        from django.db import models

        class TestTitleExtension(TitleExtension):
            content = models.CharField('Content', max_length=50)

            class Meta:
                abstract = True

        return TestTitleExtension

    @staticmethod
    def get_none_extension_class():
        class TestNoneExtension:
            pass

        return TestNoneExtension

    def test_copy_extensions(self):
        root = create_page('Root', "nav_playground.html", "en", published=True)
        page = create_page(
            'Test Page Extension', "nav_playground.html", "en",
            parent=root.get_draft_object()
        )
        subpage = create_page(
            'Test subpage Extension', "nav_playground.html", "en",
            parent=page
        )
        page = Page.objects.get(pk=page.pk)
        page_extension = MyPageExtension(extended_object=page, extra='page extension 1')
        page_extension.save()
        page.mypageextension = page_extension
        title = page.get_title_obj()
        title_extension = MyTitleExtension(extended_object=title, extra_title='title extension 1')
        title_extension.save()
        page.mytitleextension = title_extension

        subpage_extension = MyPageExtension(extended_object=subpage, extra='page extension 2')
        subpage_extension.save()
        subpage.mypageextension = subpage_extension
        subtitle = subpage.get_title_obj()
        subtitle_extension = MyTitleExtension(extended_object=subtitle, extra_title='title extension 2')
        subtitle_extension.save()
        subpage.mytitleextension = subtitle_extension

        # asserting original extensions
        self.assertEqual(len(extension_pool.get_page_extensions()), 2)
        self.assertEqual(len(extension_pool.get_title_extensions()), 2)
        copied_page = page.copy_with_descendants(target_node=None, position='last-child')

        # asserting original + copied extensions
        self.assertEqual(len(extension_pool.get_page_extensions()), 4)
        self.assertEqual(len(extension_pool.get_title_extensions()), 4)

        # testing extension content
        old_page_extensions = [page_extension, subpage_extension]
        old_title_extension = [title_extension, subtitle_extension]
        for index, new_page in enumerate([copied_page] + list(copied_page.get_descendant_pages())):
            self.assertEqual(
                extension_pool.get_page_extensions(new_page)[0].extra,
                old_page_extensions[index].extra
            )
            self.assertEqual(
                extension_pool.get_title_extensions(new_page.title_set.get(language='en'))[0].extra_title,
                old_title_extension[index].extra_title
            )
            # check that objects are actually different
            self.assertNotEqual(
                extension_pool.get_page_extensions(new_page)[0].pk,
                old_page_extensions[index].pk
            )
            self.assertNotEqual(
                extension_pool.get_title_extensions(new_page.title_set.get(language='en'))[0].pk,
                old_title_extension[index].pk
            )

        # Test deleting original page for #3987
        page.delete()
        # asserting original extensions are gone, but copied ones should still exist
        self.assertEqual(len(extension_pool.get_page_extensions()), 2)
        self.assertEqual(len(extension_pool.get_title_extensions()), 2)

    def test_copy_multitable_extensions(self):
        root = create_page('Root', "nav_playground.html", "en", published=True)
        page = create_page(
            'Test Multi-Table Page Extension', "nav_playground.html", "en",
            parent=root.get_draft_object()
        )
        subpage = create_page(
            'Test Multi-Table subpage Extension', "nav_playground.html", "en",
            parent=page
        )
        page = Page.objects.get(pk=page.pk)
        page_extension = MultiTablePageExtension(
            extended_object=page,
            extension_parent_field='page extension 1',
            multitable_extra='multi-table page extension 1'
        )
        page_extension.save()
        page.multitablepageextension = page_extension
        title = page.get_title_obj()
        title_extension = MultiTableTitleExtension(
            extended_object=title,
            extension_title_parent_field='title extension 1',
            multitable_extra_title='multi-table title extension 1'
        )
        title_extension.save()
        page.multitabletitleextension = title_extension

        subpage_extension = MultiTablePageExtension(
            extended_object=subpage,
            extension_parent_field='page extension 2',
            multitable_extra='multi-table page extension 2'
        )
        subpage_extension.save()
        subpage.multitablepageextension = subpage_extension
        subtitle = subpage.get_title_obj()
        subtitle_extension = MultiTableTitleExtension(
            extended_object=subtitle,
            extension_title_parent_field='title extension 2',
            multitable_extra_title='multi-table title extension 2'
        )
        subtitle_extension.save()
        subpage.multitabletitleextension = subtitle_extension

        # asserting original extensions
        self.assertEqual(len(extension_pool.get_page_extensions()), 2)
        self.assertEqual(len(extension_pool.get_title_extensions()), 2)

        copied_page = page.copy_with_descendants(target_node=None, position='last-child')

        # asserting original + copied extensions
        self.assertEqual(len(extension_pool.get_page_extensions()), 4)
        self.assertEqual(len(extension_pool.get_title_extensions()), 4)

        # testing extension content
        old_page_extensions = [page_extension, subpage_extension]
        old_title_extension = [title_extension, subtitle_extension]
        for index, new_page in enumerate([copied_page] + list(copied_page.get_descendant_pages())):
            copied_page_extension = extension_pool.get_page_extensions(new_page)[0]
            copied_title_extension = extension_pool.get_title_extensions(
                new_page.title_set.get(language='en')
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
                copied_title_extension.extension_title_parent_field,
                old_title_extension[index].extension_title_parent_field
            )
            self.assertEqual(
                copied_title_extension.multitable_extra_title,
                old_title_extension[index].multitable_extra_title
            )
            # check that objects are actually different
            self.assertNotEqual(
                extension_pool.get_page_extensions(new_page)[0].pk,
                old_page_extensions[index].pk
            )
            self.assertNotEqual(
                extension_pool.get_title_extensions(new_page.title_set.get(language='en'))[0].pk,
                old_title_extension[index].pk
            )

        # Test deleting original page for #3987
        page.delete()
        # asserting original extensions are gone, but copied ones should still exist
        self.assertEqual(len(extension_pool.get_page_extensions()), 2)
        self.assertEqual(len(extension_pool.get_title_extensions()), 2)

    def test_publish_page_extension(self):
        page = create_page('Test Page Extension', "nav_playground.html", "en")
        page_extension = MyPageExtension(extended_object=page, extra='page extension 1')
        page_extension.save()
        page.mypageextension = page_extension

        # publish first time
        page.publish('en')
        self.assertEqual(page_extension.extra, page.publisher_public.mypageextension.extra)
        self.assertEqual(page.get_publisher_state('en'), 0)
        # change and publish again
        page = Page.objects.get(pk=page.pk)
        page_extension = page.mypageextension
        page_extension.extra = 'page extension 1 - changed'
        page_extension.save()
        self.assertEqual(page.get_publisher_state('en', True), PUBLISHER_STATE_DIRTY)
        page.publish('en')
        self.assertEqual(page.get_publisher_state('en', True), 0)
        # delete
        page_extension.delete()
        self.assertFalse(MyPageExtension.objects.filter(pk=page_extension.pk).exists())
        self.assertEqual(page.get_publisher_state('en', True), PUBLISHER_STATE_DIRTY)

    def test_publish_multitable_page_extension(self):
        page = create_page('Test Multi-Table Page Extension', "nav_playground.html", "en")
        page_extension = MultiTablePageExtension(
            extended_object=page,
            extension_parent_field='page extension 1',
            multitable_extra='multi-table page extension 1'
        )
        page_extension.save()
        page.multitablepageextension = page_extension

        # publish first time
        page.publish('en')
        # print(dir(page))
        self.assertEqual(
            page_extension.extension_parent_field,
            page.publisher_public.multitablepageextension.extension_parent_field
        )
        self.assertEqual(
            page_extension.multitable_extra,
            page.publisher_public.multitablepageextension.multitable_extra
        )
        self.assertEqual(page.get_publisher_state('en'), 0)
        # change and publish again
        page = Page.objects.get(pk=page.pk)
        page_extension = page.multitablepageextension
        page_extension.extension_parent_field = 'page extension 1 - changed'
        page_extension.multitable_extra = 'multi-table page extension 1 - changed'
        page_extension.save()
        self.assertEqual(page.get_publisher_state('en', True), PUBLISHER_STATE_DIRTY)
        page.publish('en')
        self.assertEqual(page.get_publisher_state('en', True), 0)
        # delete
        page_extension.delete()
        self.assertFalse(MultiTablePageExtension.objects.filter(pk=page_extension.pk).exists())
        self.assertEqual(page.get_publisher_state('en', True), PUBLISHER_STATE_DIRTY)


    def test_publish_title_extension(self):
        page = create_page('Test Title Extension', "nav_playground.html", "en")
        title = page.get_title_obj()
        title_extension = MyTitleExtension(extended_object=title, extra_title='title extension 1')
        title_extension.save()
        page.mytitleextension = title_extension

        # publish first time
        page.publish('en')
        self.assertEqual(page.get_publisher_state('en'), 0)
        self.assertEqual(
            title_extension.extra_title,
            page.publisher_public.get_title_obj().mytitleextension.extra_title
        )

        # change and publish again
        page = Page.objects.get(pk=page.pk)
        title = page.get_title_obj()
        title_extension = title.mytitleextension
        title_extension.extra_title = 'title extension 1 - changed'
        title_extension.save()
        self.assertEqual(page.get_publisher_state('en', True), PUBLISHER_STATE_DIRTY)
        page.publish('en')
        self.assertEqual(page.get_publisher_state('en', True), 0)

        # delete
        title_extension.delete()
        self.assertFalse(MyTitleExtension.objects.filter(pk=title_extension.pk).exists())

    def test_publish_mutlitable_title_extension(self):
        page = create_page('Test Title Extension', "nav_playground.html", "en")
        title = page.get_title_obj()
        title_extension = MultiTableTitleExtension(
            extended_object=title,
            extension_title_parent_field='title extension 1',
            multitable_extra_title='multi table title extension 1'
        )
        title_extension.save()
        page.multitabletitleextension = title_extension

        # publish first time
        page.publish('en')
        self.assertEqual(page.get_publisher_state('en'), 0)
        self.assertEqual(
            title_extension.extension_title_parent_field,
            page.publisher_public.get_title_obj().multitabletitleextension.extension_title_parent_field
        )
        self.assertEqual(
            title_extension.multitable_extra_title,
            page.publisher_public.get_title_obj().multitabletitleextension.multitable_extra_title
        )

        # change and publish again
        page = Page.objects.get(pk=page.pk)
        title = page.get_title_obj()
        title_extension = title.multitabletitleextension
        title_extension.extension_title_parent_field = 'title extension 1 - changed'
        title_extension.multitable_extra_title = 'multitable title extension 1 - changed'
        title_extension.save()
        self.assertEqual(page.get_publisher_state('en', True), PUBLISHER_STATE_DIRTY)
        page.publish('en')
        self.assertEqual(page.get_publisher_state('en', True), 0)

        # delete
        title_extension.delete()
        self.assertFalse(MultiTableTitleExtension.objects.filter(pk=title_extension.pk).exists())

    def test_fallback_title_extension(self):
        page = create_page('Test Fallback Title Extension', "nav_playground.html", "en")
        title_en = page.get_title_obj('en')
        title_extension_en = MyTitleExtension(
            extended_object=title_en,
            extra_title='title extension EN'
        )
        title_extension_en.save()
        page.publish('en')

        self.assertEqual(
            page.get_title_obj('en', True).mytitleextension.extra_title,
            'title extension EN'
        )

        title_de = create_title(title="de page", language="de", page=page)
        title_extension_de = MyTitleExtension(
            extended_object=title_de,
            extra_title='title extension DE'
        )
        title_extension_de.save()
        page.publish('de')

        self.assertEqual(
            page.get_title_obj('de', True).mytitleextension.extra_title,
            'title extension DE'
        )


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
                'change_mypageextension', 'change_mytitleextension',
                'add_mypageextension', 'add_mytitleextension',
                'delete_mypageextension', 'delete_mytitleextension',
            ]
        )]
        self.site = Site.objects.get(pk=1)
        self.page = create_page(
            'My Extension Page', 'nav_playground.html', 'en',
            site=self.site, created_by=self.admin)
        self.page_title = self.page.get_title_obj('en')
        create_title('de', 'de title', self.page)
        self.page_extension = MyPageExtension.objects.create(
            extended_object=self.page,
            extra="page extension text")
        self.title_extension = MyTitleExtension.objects.create(
            extended_object=self.page.get_title_obj(),
            extra_title="title extension text")

        self.page_without_extension = create_page(
            'A Page', 'nav_playground.html', 'en',
            site=self.site, created_by=self.admin)
        self.page_title_without_extension = self.page_without_extension.get_title_obj()

    def test_duplicate_extensions(self):
        with self.login_user_context(self.admin):
            # create page copy
            page_data = {
                'title': 'type1', 'slug': 'type1', '_save': 1, 'template': 'nav_playground.html',
                'site': 1, 'language': 'en', 'source': self.page.pk,
            }
            self.assertEqual(Page.objects.all().count(), 2)
            self.assertEqual(MyPageExtension.objects.all().count(), 1)
            self.assertEqual(MyTitleExtension.objects.all().count(), 1)
            response = self.client.post(
                self.get_admin_url(Page, 'duplicate', self.page.pk),
                data=page_data,
            )
            # Check that page and its extensions have been copied
            self.assertRedirects(response, self.get_admin_url(Page, 'changelist'))
            self.assertEqual(Page.objects.all().count(), 3)
            self.assertEqual(MyPageExtension.objects.all().count(), 2)
            self.assertEqual(MyTitleExtension.objects.all().count(), 2)

    def test_page_type_extensions(self):
        with self.login_user_context(self.admin):
            # create page copy
            page_data = {
                'title': 'type1', 'slug': 'type1', '_save': 1, 'template': 'nav_playground.html',
                'site': 1, 'language': 'en', 'source': self.page.pk,
            }
            self.assertEqual(Page.objects.all().count(), 2)
            self.assertEqual(MyPageExtension.objects.all().count(), 1)
            self.assertEqual(MyTitleExtension.objects.all().count(), 1)
            response = self.client.post(
                self.get_admin_url(PageType, 'add'),
                data=page_data,
            )
            self.assertRedirects(response, self.get_admin_url(PageType, 'changelist'))
            # Check that new page type has extensions from source page
            self.assertEqual(Page.objects.all().count(), 4)
            self.assertEqual(Page.objects.filter(is_page_type=True).count(), 2)
            self.assertEqual(MyPageExtension.objects.all().count(), 2)
            self.assertEqual(MyTitleExtension.objects.all().count(), 2)

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
            self.assertFalse(
                MyPageExtension.objects.filter(extended_object=self.page_without_extension).exists()
            )
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
                response,
                admin_reverse('extensionapp_mypageextension_change', args=(self.page_extension.pk,))
            )

            # saving an extension should work without the GET parameter
            post_data = {
                'extra': 'my extra text'
            }
            self.client.post(
                admin_reverse('extensionapp_mypageextension_change', args=(self.page_extension.pk,)),
                post_data, follow=True
            )
            self.assertTrue(
                MyPageExtension.objects.filter(extra='my extra text', pk=self.page_extension.pk).exists()
            )

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

    def test_toolbar_title_extension(self):
        old_toolbars = deepcopy(toolbar_pool.toolbars)

        class SampleExtension(ExtensionToolbar):
            model = MyTitleExtension

            def populate(self):
                current_page_menu = self._setup_extension_toolbar()
                if current_page_menu:
                    position = 0
                    urls = self.get_title_extension_admin()
                    for title_extension, url in urls:
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

    def test_admin_title_extension(self):
        with self.login_user_context(self.admin):
            # add a new extension
            response = self.client.get(
                admin_reverse(
                    'extensionapp_mytitleextension_add'
                ) + '?extended_object=%s' % self.page_title_without_extension.pk
            )
            self.assertEqual(response.status_code, 200)
            # make sure there is no extension yet
            self.assertFalse(
                MyTitleExtension.objects.filter(extended_object=self.page_title_without_extension).exists()
            )
            post_data = {
                'extra_title': 'my extra title'
            }
            self.client.post(
                admin_reverse(
                    'extensionapp_mytitleextension_add'
                ) + '?extended_object=%s' % self.page_title_without_extension.pk,
                post_data, follow=True
            )
            created_title_extension = MyTitleExtension.objects.get(
                extended_object=self.page_title_without_extension
            )

            # can delete extension
            self.client.post(
                admin_reverse('extensionapp_mytitleextension_delete', args=(created_title_extension.pk,)),
                {'post': 'yes'}, follow=True
            )
            self.assertFalse(
                MyTitleExtension.objects.filter(extended_object=self.page_title_without_extension).exists()
            )

            # accessing the add view on a page that already has an extension should redirect
            response = self.client.get(
                admin_reverse('extensionapp_mytitleextension_add') + '?extended_object=%s' % self.page_title.pk
            )
            self.assertRedirects(
                response,
                admin_reverse('extensionapp_mytitleextension_change', args=(self.title_extension.pk,))
            )

            # saving an extension should work without the GET parameter
            post_data = {
                'extra_title': 'my extra text'
            }
            self.client.post(
                admin_reverse('extensionapp_mytitleextension_change', args=(self.title_extension.pk,)),
                post_data, follow=True
            )
            self.assertTrue(
                MyTitleExtension.objects.filter(extra_title='my extra text', pk=self.title_extension.pk).exists()
            )

        with self.login_user_context(self.no_page_permission_user):
            # can't save if user does not have permissions to change the page
            post_data = {
                'extra_title': 'try to change extra text'
            }
            response = self.client.post(
                admin_reverse('extensionapp_mytitleextension_change', args=(self.title_extension.pk,)),
                post_data, follow=True
            )
            self.assertEqual(response.status_code, 403)

            # can't delete without page permission
            response = self.client.post(
                admin_reverse('extensionapp_mytitleextension_delete', args=(self.title_extension.pk,)),
                {'post': 'yes'}, follow=True
            )
            self.assertEqual(response.status_code, 403)
            self.assertTrue(MyTitleExtension.objects.filter(extended_object=self.page_title).exists())
