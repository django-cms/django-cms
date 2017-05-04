# -*- coding: utf-8 -*-
from djangocms_text_ckeditor.models import Text
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.management.base import CommandError
from django.core.management import call_command
from django.core.urlresolvers import reverse

from cms.api import create_page, add_plugin, create_title
from cms.constants import PUBLISHER_STATE_PENDING, PUBLISHER_STATE_DEFAULT, PUBLISHER_STATE_DIRTY
from cms.management.commands.subcommands.publisher_publish import PublishCommand
from cms.models import CMSPlugin, Title
from cms.models.pagemodel import Page
from cms.plugin_pool import plugin_pool
from cms.test_utils.testcases import CMSTestCase as TestCase
from cms.test_utils.util.context_managers import StdoutOverride
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import force_language
from cms.utils.urlutils import admin_reverse


class PublisherCommandTests(TestCase):
    """
    Tests for the publish command
    """

    def test_command_line_should_raise_without_superuser(self):
        with self.assertRaises(CommandError):
            com = PublishCommand()
            com.handle()

    def test_command_line_publishes_zero_pages_on_empty_db(self):
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish')
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 0)
        self.assertEqual(published_from_output, 0)

    def test_command_line_ignores_draft_page(self):
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        create_page("The page!", "nav_playground.html", "en", published=False)

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish')
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 0)
        self.assertEqual(published_from_output, 0)

        self.assertEqual(Page.objects.public().count(), 0)

    def test_command_line_publishes_draft_page(self):
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        create_page("The page!", "nav_playground.html", "en", published=False)

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish', include_unpublished=True)
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 1)
        self.assertEqual(published_from_output, 1)

        self.assertEqual(Page.objects.public().count(), 1)

    def test_command_line_publishes_selected_language(self):
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        page = create_page("en title", "nav_playground.html", "en")
        title = create_title('de', 'de title', page)
        title.published = True
        title.save()
        title = create_title('fr', 'fr title', page)
        title.published = True
        title.save()

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish', language='de')
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 1)
        self.assertEqual(published_from_output, 1)

        self.assertEqual(Page.objects.public().count(), 1)
        public = Page.objects.public()[0]
        languages = sorted(public.title_set.values_list('language', flat=True))
        self.assertEqual(languages, ['de'])

    def test_command_line_publishes_selected_language_drafts(self):
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        page = create_page("en title", "nav_playground.html", "en")
        title = create_title('de', 'de title', page)
        title.published = False
        title.save()
        title = create_title('fr', 'fr title', page)
        title.published = False
        title.save()

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish', language='de', include_unpublished=True)
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 1)
        self.assertEqual(published_from_output, 1)

        self.assertEqual(Page.objects.public().count(), 1)
        public = Page.objects.public()[0]
        languages = sorted(public.title_set.values_list('language', flat=True))
        self.assertEqual(languages, ['de'])

    def test_table_name_patching(self):
        """
        This tests the plugin models patching when publishing from the command line
        """
        User = get_user_model()
        User.objects.create_superuser('djangocms', 'cms@example.com', '123456')
        create_page("The page!", "nav_playground.html", "en", published=True)
        draft = Page.objects.drafts()[0]
        draft.reverse_id = 'a_test' # we have to change *something*
        draft.save()
        add_plugin(draft.placeholders.get(slot=u"body"),
                   u"TextPlugin", u"en", body="Test content")
        draft.publish('en')
        add_plugin(draft.placeholders.get(slot=u"body"),
                   u"TextPlugin", u"en", body="Test content")

        # Manually undoing table name patching
        Text._meta.db_table = 'djangocms_text_ckeditor_text'
        plugin_pool.patched = False

        with StdoutOverride():
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish')
        not_drafts = len(Page.objects.filter(publisher_is_draft=False))
        drafts = len(Page.objects.filter(publisher_is_draft=True))
        self.assertEqual(not_drafts, 1)
        self.assertEqual(drafts, 1)

    def test_command_line_publishes_one_page(self):
        """
        Publisher always creates two Page objects for every CMS page,
        one is_draft and one is_public.

        The public version of the page can be either published or not.

        This bit of code uses sometimes manager methods and sometimes manual
        filters on purpose (this helps test the managers)
        """
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        # Now, let's create a page. That actually creates 2 Page objects
        create_page("The page!", "nav_playground.html", "en", published=True)
        draft = Page.objects.drafts()[0]
        draft.reverse_id = 'a_test' # we have to change *something*
        draft.save()

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish')
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 1)
        self.assertEqual(published_from_output, 1)
        # Sanity check the database (we should have one draft and one public)
        not_drafts = len(Page.objects.filter(publisher_is_draft=False))
        drafts = len(Page.objects.filter(publisher_is_draft=True))
        self.assertEqual(not_drafts, 1)
        self.assertEqual(drafts, 1)

        # Now check that the non-draft has the attribute we set to the draft.
        non_draft = Page.objects.public()[0]
        self.assertEqual(non_draft.reverse_id, 'a_test')

    def test_command_line_publish_multiple_languages(self):
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        # Create a draft page with two published titles
        page = create_page(u"The page!", "nav_playground.html", "en", published=False)
        title = create_title('de', 'ja', page)
        title.published = True
        title.save()
        title = create_title('fr', 'non', page)
        title.published = True
        title.save()

        with StdoutOverride():
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish')

        public = Page.objects.public()[0]
        languages = sorted(public.title_set.values_list('language', flat=True))
        self.assertEqual(languages, ['de', 'fr'])

    def test_command_line_publish_one_site(self):
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        siteA = Site.objects.create(domain='a.example.com', name='a.example.com')
        siteB = Site.objects.create(domain='b.example.com', name='b.example.com')

        #example.com
        create_page(u"example.com homepage", "nav_playground.html", "en", published=True)
        #a.example.com
        create_page(u"a.example.com homepage", "nav_playground.html", "de", site=siteA, published=True)
        #b.example.com
        create_page(u"b.example.com homepage", "nav_playground.html", "de", site=siteB, published=True)
        create_page(u"b.example.com about", "nav_playground.html", "nl", site=siteB, published=True)

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish', site=siteB.id)
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 2)
        self.assertEqual(published_from_output, 2)

    def test_command_line_publish_multiple_languages_check_count(self):
        """
        Publishing one page with multiple languages still counts
        as one page. This test case checks whether it works
        as expected.
        """
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        # Now, let's create a page with 2 languages.
        page = create_page("en title", "nav_playground.html", "en", published=True)
        create_title("de", "de title", page)
        page.publish("de")

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish')
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 1)
        self.assertEqual(published_from_output, 1)

    def tearDown(self):
        plugin_pool.patched = False
        plugin_pool.set_plugin_meta()


class PublishingTests(TestCase):
    def create_page(self, title=None, **kwargs):
        return create_page(title or self._testMethodName,
                           "nav_playground.html", "en", **kwargs)

    def test_publish_home(self):
        name = self._testMethodName
        page = self.create_page(name, published=False)
        self.assertFalse(page.publisher_public_id)
        self.assertEqual(Page.objects.all().count(), 1)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.post(admin_reverse("cms_page_publish_page", args=[page.pk, 'en']))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response['Location'].endswith("/en/?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')))

    def test_publish_single(self):
        name = self._testMethodName
        page = self.create_page(name, published=False)
        self.assertFalse(page.is_published('en'))

        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published("en")
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectDoesNotExist(public, title_set__title=name)
        self.assertObjectDoesNotExist(published, title_set__title=name)

        page.publish("en")

        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published("en")

        self.assertTrue(page.is_published('en'))
        self.assertEqual(page.get_publisher_state("en"), PUBLISHER_STATE_DEFAULT)
        self.assertIsNotNone(page.publisher_public)
        self.assertTrue(page.publisher_public_id)

        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(public, title_set__title=name)
        self.assertObjectExist(published, title_set__title=name)

        page = Page.objects.get(pk=page.pk)

        self.assertEqual(page.get_publisher_state("en"), 0)

    def test_publish_admin(self):
        page = self.create_page("test_admin", published=False)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.post(admin_reverse("cms_page_publish_page", args=[page.pk, 'en']))
            self.assertEqual(response.status_code, 302)
        page = Page.objects.get(pk=page.pk)

        self.assertEqual(page.get_publisher_state('en'), 0)

    def test_publish_wrong_lang(self):
        page = self.create_page("test_admin", published=False)
        superuser = self.get_superuser()
        with self.settings(
            LANGUAGES=(('de', 'de'), ('en', 'en')),
            CMS_LANGUAGES={1: [{'code': 'en', 'name': 'en', 'fallbacks': ['fr', 'de'], 'public': True}]}
        ):
            with self.login_user_context(superuser):
                with force_language('de'):
                    response = self.client.post(admin_reverse("cms_page_publish_page", args=[page.pk, 'en']))
        self.assertEqual(response.status_code, 302)
        page = Page.objects.get(pk=page.pk)

    def test_publish_missing_page(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.post(admin_reverse("cms_page_publish_page", args=[999999, 'en']))
            self.assertEqual(response.status_code, 404)

    def test_publish_child_first(self):
        parent = self.create_page('parent', published=False)
        child = self.create_page('child', published=False, parent=parent)
        parent = parent.reload()
        self.assertFalse(parent.is_published('en'))
        self.assertFalse(child.is_published('en'))

        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published('en')

        for name in ('parent', 'child'):
            self.assertObjectExist(drafts, title_set__title=name)
            self.assertObjectDoesNotExist(public, title_set__title=name)
            self.assertObjectDoesNotExist(published, title_set__title=name)

        child.publish("en")
        child = child.reload()
        self.assertTrue(child.is_published("en"))
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_PENDING)
        self.assertIsNone(child.publisher_public)

        # Since we have no parent, the state is otherwise unchanged
        for name in ('parent', 'child'):
            self.assertObjectExist(drafts, title_set__title=name)
            self.assertObjectDoesNotExist(public, title_set__title=name)
            self.assertObjectDoesNotExist(published, title_set__title=name)
        parent.publish("en")
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published('en')
        # Cascade publish for all pending descendants
        for name in ('parent', 'child'):
            self.assertObjectExist(drafts, title_set__title=name)
            page = drafts.get(title_set__title=name)
            self.assertTrue(page.is_published("en"), name)
            self.assertEqual(page.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT, name)
            self.assertIsNotNone(page.publisher_public, name)
            self.assertTrue(page.publisher_public.is_published('en'), name)

            self.assertObjectExist(public, title_set__title=name)
            self.assertObjectExist(published, title_set__title=name)

    def test_simple_publisher(self):
        """
        Creates the stuff needed for these tests.
        Please keep this up-to-date (the docstring!)

                A
               / \
              B  C
        """
        # Create a simple tree of 3 pages
        pageA = create_page("Page A", "nav_playground.html", "en",
                            published=True)
        pageB = create_page("Page B", "nav_playground.html", "en", parent=pageA,
                            published=True)
        pageC = create_page("Page C", "nav_playground.html", "en", parent=pageA,
                            published=False)
        # Assert A and B are published, C unpublished
        self.assertTrue(pageA.publisher_public_id)
        self.assertTrue(pageB.publisher_public_id)
        self.assertTrue(not pageC.publisher_public_id)
        self.assertEqual(len(Page.objects.public().published("en")), 2)

        # Let's publish C now.
        pageC.publish("en")

        # Assert all are published
        self.assertTrue(pageA.publisher_public_id)
        self.assertTrue(pageB.publisher_public_id)
        self.assertTrue(pageC.publisher_public_id)
        self.assertEqual(len(Page.objects.public().published("en")), 3)

    def test_i18n_publishing(self):
        page = self.create_page('parent', published=True)
        self.assertEqual(Title.objects.all().count(), 2)
        create_title("de", "vater", page)
        self.assertEqual(Title.objects.all().count(), 3)
        self.assertEqual(Title.objects.filter(published=True).count(), 2)
        page.publish('de')
        self.assertEqual(Title.objects.all().count(), 4)
        self.assertEqual(Title.objects.filter(published=True).count(), 4)


    def test_publish_ordering(self):
        page = self.create_page('parent', published=True)
        pageA = self.create_page('pageA', parent=page, published=True)
        pageC = self.create_page('pageC', parent=page, published=True)
        pageB = self.create_page('pageB', parent=page, published=True)
        page = page.reload()
        pageB.move_page(pageA, 'right')
        pageB.publish("en")
        # pageC needs reload since B has swapped places with it
        pageC.reload().publish("en")
        pageA.publish('en')

        drafts = Page.objects.drafts().order_by('path')
        draft_titles = [(p.get_title('en'), p.path) for p in drafts]
        self.assertEqual([('parent', "0001"),
                              ('pageA', "00010001"),
                              ('pageB', "00010002"),
                              ('pageC', "00010003")], draft_titles)
        public = Page.objects.public().order_by('path')
        public_titles = [(p.get_title('en'), p.path) for p in public]
        self.assertEqual([('parent', "0002"),
                              ('pageA', "00020001"),
                              ('pageB', "00020002"),
                              ('pageC', "00020003")], public_titles)

        page.publish('en')

        drafts = Page.objects.drafts().order_by('path')
        draft_titles = [(p.get_title('en'), p.path) for p in drafts]
        self.assertEqual([('parent', "0001"),
                              ('pageA', "00010001"),
                              ('pageB', "00010002"),
                              ('pageC', "00010003")], draft_titles)
        public = Page.objects.public().order_by('path')
        public_titles = [(p.get_title('en'), p.path) for p in public]
        self.assertEqual([('parent', "0002"),
                              ('pageA', "00020001"),
                              ('pageB', "00020002"),
                              ('pageC', "00020003")], public_titles)

    def test_publish_ordering2(self):
        page = self.create_page('parent', published=False)
        pageA = self.create_page('pageA', published=False)
        pageC = self.create_page('pageC', published=False, parent=pageA)
        pageB = self.create_page('pageB', published=False, parent=pageA)
        page = page.reload()
        pageA = pageA.reload()
        pageB = pageB.reload()
        pageC = pageC.reload()
        pageA.publish('en')
        page = page.reload()
        pageB = pageB.reload()
        pageC = pageC.reload()
        pageB.publish('en')
        page = page.reload()
        pageC = pageC.reload()
        pageC.publish('en')
        page = page.reload()
        page.publish('en')

        drafts = Page.objects.filter(publisher_is_draft=True).order_by('path')
        publics = Page.objects.filter(publisher_is_draft=False).order_by('path')

        x = 0
        for draft in drafts:
            self.assertEqual(draft.publisher_public_id, publics[x].pk)
            x += 1

    def test_unpublish_unpublish(self):
        name = self._testMethodName
        page = self.create_page(name, published=True)
        drafts = Page.objects.drafts()
        published = Page.objects.public().published("en")
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(published, title_set__title=name)

        page.unpublish('en')
        self.assertFalse(page.is_published('en'))
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectDoesNotExist(published, title_set__title=name)

        page.publish('en')
        self.assertTrue(page.publisher_public_id)
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(published, title_set__title=name)

    def test_delete_title_unpublish(self):
        page = self.create_page('test', published=True)
        sub_page = self.create_page('test2', published=True, parent=page)
        self.assertTrue(sub_page.publisher_public.is_published('en'))
        page.reload().title_set.all().delete()
        self.assertFalse(sub_page.publisher_public.is_published('en', force_reload=True))

    def test_modify_child_while_pending(self):
        home = self.create_page("Home", published=True, in_navigation=True)
        child = self.create_page("Child", published=True, parent=home,
                                 in_navigation=False)
        home = home.reload()
        home.unpublish('en')
        self.assertEqual(Title.objects.count(), 4)
        child = child.reload()
        self.assertFalse(child.publisher_public.is_published('en'))
        self.assertFalse(child.in_navigation)
        self.assertFalse(child.publisher_public.in_navigation)

        child.in_navigation = True
        child.save()
        child.publish('en')
        child = self.reload(child)
        self.assertEqual(Title.objects.count(), 4)

        self.assertTrue(child.is_published('en'))
        self.assertFalse(child.publisher_public.is_published('en'))
        self.assertTrue(child.in_navigation)
        self.assertTrue(child.publisher_public.in_navigation)
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_PENDING)

        home.publish('en')
        child = self.reload(child)
        self.assertTrue(child.is_published('en'))
        self.assertTrue(child.publisher_public_id)
        self.assertTrue(child.publisher_public.in_navigation)
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

    def test_republish_with_descendants(self):
        home = self.create_page("Home", published=True)
        child = self.create_page("Child", published=True, parent=home)
        gc = self.create_page("GC", published=True, parent=child)
        self.assertTrue(child.is_published("en"))
        self.assertTrue(gc.is_published('en'))
        home = home.reload()
        home.unpublish('en')
        child = self.reload(child)
        gc = self.reload(gc)
        self.assertTrue(child.is_published("en"))
        self.assertTrue(gc.is_published("en"))
        self.assertFalse(child.publisher_public.is_published("en"))
        self.assertFalse(gc.publisher_public.is_published('en'))
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_PENDING)
        self.assertEqual(gc.get_publisher_state('en'), PUBLISHER_STATE_PENDING)

        home.publish('en')
        child = self.reload(child)
        gc = self.reload(gc)

        self.assertTrue(child.publisher_public_id)
        self.assertTrue(gc.is_published('en'))
        self.assertTrue(child.is_published('en'))
        self.assertTrue(gc.publisher_public_id)
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)
        self.assertEqual(gc.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

    def test_republish_with_dirty_children(self):
        home = self.create_page("Home", published=True)
        dirty1 = self.create_page("Dirty1", published=True, parent=home)
        dirty2 = self.create_page("Dirty2", published=True, parent=home)
        home = self.reload(home)
        dirty1 = self.reload(dirty1)
        dirty2 = self.reload(dirty2)
        dirty1.in_navigation = True
        dirty1.save()
        home.unpublish('en')
        dirty2.in_navigation = True
        dirty2.save()
        dirty1 = self.reload(dirty1)
        dirty2 = self.reload(dirty2)
        self.assertTrue(dirty1.is_published)
        self.assertTrue(dirty2.publisher_public_id)
        self.assertEqual(dirty1.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)
        self.assertEqual(dirty2.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)

        home = self.reload(home)
        with self.assertNumQueries(FuzzyInt(0, 100)):
            home.publish('en')
        dirty1 = self.reload(dirty1)
        dirty2 = self.reload(dirty2)
        self.assertTrue(dirty1.is_published("en"))
        self.assertTrue(dirty2.is_published("en"))
        self.assertTrue(dirty1.publisher_public.is_published("en"))
        self.assertTrue(dirty2.publisher_public.is_published("en"))
        self.assertEqual(dirty1.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)
        self.assertEqual(dirty2.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)

    def test_republish_with_unpublished_child(self):
        """
        Unpub1 was never published, and unpub2 has been unpublished after the
        fact. None of the grandchildren should become published.
        """
        home = self.create_page("Home", published=True)
        unpub1 = self.create_page("Unpub1", published=False, parent=home)
        unpub2 = self.create_page("Unpub2", published=True, parent=home)
        gc1 = self.create_page("GC1", published=True, parent=unpub1)
        gc2 = self.create_page("GC2", published=True, parent=unpub2)
        self.assertFalse(gc1.publisher_public_id)
        self.assertFalse(gc1.publisher_public_id)
        self.assertTrue(gc1.is_published('en'))
        self.assertTrue(gc2.is_published('en'))

        home = self.reload(home)
        home.unpublish('en')

        unpub1 = self.reload(unpub1)
        unpub2 = self.reload(unpub2)
        unpub2.unpublish('en')  # Just marks this as not published

        for page in (unpub1, unpub2):
            self.assertFalse(page.is_published('en'), page)
            self.assertEqual(page.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)
        self.assertIsNone(unpub1.publisher_public)
        self.assertIsNotNone(unpub2.publisher_public)
        self.assertFalse(unpub2.publisher_public.is_published('en'))

        gc1 = self.reload(gc1)
        gc2 = self.reload(gc2)
        for page in (gc1, gc2):
            self.assertTrue(page.is_published('en'))
            self.assertEqual(page.get_publisher_state('en'), PUBLISHER_STATE_PENDING)
        self.assertIsNone(gc1.publisher_public)
        self.assertIsNotNone(gc2.publisher_public)
        self.assertFalse(gc2.publisher_public.is_published('en'))

    def test_unpublish_with_descendants(self):
        page = self.create_page("Page", published=True)
        child = self.create_page("Child", parent=page, published=True)
        self.create_page("Grandchild", parent=child, published=True)
        page = page.reload()
        child.reload()
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published("en")
        self.assertEqual(published.count(), 3)
        self.assertEqual(page.get_descendant_count(), 2)
        base = reverse('pages-root')

        for url in (base, base + 'child/', base + 'child/grandchild/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

        for title in ('Page', 'Child', 'Grandchild'):
            self.assertObjectExist(drafts, title_set__title=title)
            self.assertObjectExist(public, title_set__title=title)
            self.assertObjectExist(published, title_set__title=title)
            item = drafts.get(title_set__title=title)
            self.assertTrue(item.publisher_public_id)
            self.assertEqual(item.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

        self.assertTrue(page.unpublish('en'), 'Unpublish was not successful')
        self.assertFalse(page.is_published('en'))
        cache.clear()
        for url in (base, base + 'child/', base + 'child/grandchild/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

        for title in ('Page', 'Child', 'Grandchild'):
            self.assertObjectExist(drafts, title_set__title=title)
            self.assertObjectExist(public, title_set__title=title)
            self.assertObjectDoesNotExist(published, title_set__title=title)
            item = drafts.get(title_set__title=title)
            if title == 'Page':
                self.assertFalse(item.is_published("en"))
                self.assertFalse(item.publisher_public.is_published("en"))
                # Not sure what the proper state of these are after unpublish
                #self.assertEqual(page.publisher_state, PUBLISHER_STATE_DEFAULT)
                self.assertTrue(page.is_dirty('en'))
            else:
                # The changes to the published subpages are simply that the
                # published flag of the PUBLIC instance goes to false, and the
                # publisher state is set to mark waiting for parent
                self.assertTrue(item.is_published('en'), title)
                self.assertFalse(item.publisher_public.is_published('en'), title)
                self.assertEqual(item.get_publisher_state('en'), PUBLISHER_STATE_PENDING,
                                 title)
                self.assertTrue(item.is_dirty('en'), title)

    def test_unpublish_with_dirty_descendants(self):
        page = self.create_page("Page", published=True)
        child = self.create_page("Child", parent=page, published=True)
        gchild = self.create_page("Grandchild", parent=child, published=True)
        child.in_navigation = True
        child.save()

        self.assertTrue(child.is_dirty("en"))
        self.assertFalse(gchild.is_dirty('en'))
        self.assertTrue(child.publisher_public.is_published('en'))
        self.assertTrue(gchild.publisher_public.is_published('en'))

        page.reload().unpublish('en')
        child = self.reload(child)
        gchild = self.reload(gchild)
        # Descendants become dirty after unpublish
        self.assertTrue(child.is_dirty('en'))
        self.assertTrue(gchild.is_dirty('en'))
        # However, their public version is still removed no matter what
        self.assertFalse(child.publisher_public.is_published('en'))
        self.assertFalse(gchild.publisher_public.is_published('en'))

    def test_prepublish_descendants(self):
        page = self.create_page("Page", published=True)
        child_1 = self.create_page("Child", parent=page, published=False)
        child_1_2 = self.create_page("Grandchild2", parent=child_1, published=False)

        self.create_page("Grandchild3", parent=child_1, published=True)

        # Reload "Child" page because it's tree attributes changed when adding
        # children to it above.
        child_1 = child_1.reload()

        # Create the first child of "Child" page as a published root node
        child_1_1 = self.create_page("Grandchild", published=True)
        # Move first child to "Child"
        child_1_1.move_page(target=child_1, position='last-child')
        # Publish first child
        child_1_1.publish('en')

        # Assert "Child" page is not published (we never published it)
        self.assertFalse(child_1.is_published('en'))
        # Assert "first child" is published (we published above)
        self.assertTrue(child_1_1.is_published('en'))
        # Assert "first child" is in pending state because
        # it's parent the "Child" page is not published.
        self.assertEqual(child_1_1.get_publisher_state('en'), PUBLISHER_STATE_PENDING)

        # Publish "Child page"
        child_1.publish('en')
        # Publish "second child"
        child_1_2.publish('en')

        self.assertTrue(child_1.is_published("en"))
        self.assertTrue(child_1_1.is_published("en"))
        # Assert "first child" is no longer in pending state
        # and instead is in published state.
        self.assertEqual(child_1_1.get_publisher_state('en', force_reload=True), PUBLISHER_STATE_DEFAULT)

        draft_tree_path = child_1_1.path[:4]
        live_tree_path = child_1_1.publisher_public.path[:4]

        # Make sure the draft and live child nodes are on separate trees
        self.assertNotEqual(draft_tree_path, live_tree_path)

        # However they should share the same branch path
        self.assertEqual(child_1_1.path[4:], child_1_1.publisher_public.path[4:])
        self.assertEqual(child_1_1.depth, child_1_1.publisher_public.depth)

    def test_republish_multiple_root(self):
        # TODO: The paths do not match expected behaviour
        home = self.create_page("Page", published=True)
        other = self.create_page("Another Page", published=True)
        child = self.create_page("Child", published=True, parent=home)
        child2 = self.create_page("Child", published=True, parent=other)
        self.assertTrue(Page.objects.filter(is_home=True).count(), 2)
        self.assertTrue(home.is_home)

        home = home.reload()
        self.assertTrue(home.publisher_public.is_home)
        root = reverse('pages-root')
        self.assertEqual(home.get_absolute_url(), root)
        self.assertEqual(home.get_public_object().get_absolute_url(), root)
        self.assertEqual(child.get_absolute_url(), root + 'child/')
        self.assertEqual(child.get_public_object().get_absolute_url(), root + 'child/')
        self.assertEqual(other.get_absolute_url(), root + 'another-page/')
        self.assertEqual(other.get_public_object().get_absolute_url(), root + 'another-page/')
        self.assertEqual(child2.get_absolute_url(), root + 'another-page/child/')
        self.assertEqual(child2.get_public_object().get_absolute_url(), root + 'another-page/child/')
        home = self.reload(home)
        home.unpublish('en')
        home = self.reload(home)
        other = self.reload(other)
        child = self.reload(child)
        child2 = self.reload(child2)
        self.assertFalse(home.is_home)
        self.assertFalse(home.publisher_public.is_home)
        self.assertTrue(other.is_home)
        self.assertTrue(other.publisher_public.is_home)

        self.assertEqual(other.get_absolute_url(), root)
        self.assertEqual(other.get_public_object().get_absolute_url(), root)
        self.assertEqual(home.get_absolute_url(), root + 'page/')
        self.assertEqual(home.get_public_object().get_absolute_url(), root + 'page/')

        self.assertEqual(child.get_absolute_url(), root + 'page/child/')
        self.assertEqual(child.get_public_object().get_absolute_url(), root + 'page/child/')
        self.assertEqual(child2.get_absolute_url(), root + 'child/')
        self.assertEqual(child2.get_public_object().get_absolute_url(), root + 'child/')
        home.publish('en')
        home = self.reload(home)
        other = self.reload(other)
        child = self.reload(child)
        child2 = self.reload(child2)
        self.assertTrue(home.is_home)
        self.assertTrue(home.publisher_public.is_home)
        self.assertEqual(home.get_absolute_url(), root)
        self.assertEqual(home.get_public_object().get_absolute_url(), root)
        self.assertEqual(child.get_absolute_url(), root + 'child/')
        self.assertEqual(child.get_public_object().get_absolute_url(), root + 'child/')
        self.assertEqual(other.get_absolute_url(), root + 'another-page/')
        self.assertEqual(other.get_public_object().get_absolute_url(), root + 'another-page/')
        self.assertEqual(child2.get_absolute_url(), root + 'another-page/child/')
        self.assertEqual(child2.get_public_object().get_absolute_url(), root + 'another-page/child/')

    def test_revert_contents(self):
        user = self.get_superuser()
        page = create_page("Page", "nav_playground.html", "en", published=True,
                           created_by=user)
        placeholder = page.placeholders.get(slot=u"body")
        deleted_plugin = add_plugin(placeholder, u"TextPlugin", u"en", body="Deleted content")
        text_plugin = add_plugin(placeholder, u"TextPlugin", u"en", body="Public content")
        page.publish('en')

        # Modify and delete plugins
        text_plugin.body = "<p>Draft content</p>"
        text_plugin.save()
        deleted_plugin.delete()
        self.assertEqual(CMSPlugin.objects.count(), 3)

        # Now let's revert and restore
        page.revert_to_live('en')
        self.assertEqual(page.get_publisher_state("en"), PUBLISHER_STATE_DEFAULT)

        self.assertEqual(CMSPlugin.objects.count(), 4)
        plugins = CMSPlugin.objects.filter(placeholder__page=page)
        self.assertEqual(plugins.count(), 2)

        plugins = [plugin.get_plugin_instance()[0] for plugin in plugins]
        self.assertEqual(plugins[0].body, "Deleted content")
        self.assertEqual(plugins[1].body, "Public content")

    def test_revert_move(self):
        parent = create_page("Parent", "nav_playground.html", "en", published=True)
        parent_url = parent.get_absolute_url()
        page = create_page("Page", "nav_playground.html", "en", published=True,
                           parent=parent)
        other = create_page("Other", "nav_playground.html", "en", published=True)
        other_url = other.get_absolute_url()

        child = create_page("Child", "nav_playground.html", "en", published=True,
                            parent=page)
        parent = parent.reload()
        page = page.reload()
        self.assertEqual(page.get_absolute_url(), parent_url + "page/")
        self.assertEqual(child.get_absolute_url(), parent_url + "page/child/")

        # Now let's move it (and the child)
        page.move_page(other)
        page = self.reload(page)
        child = self.reload(child)
        self.assertEqual(page.get_absolute_url(), other_url + "page/")
        self.assertEqual(child.get_absolute_url(), other_url + "page/child/")
        # Public version changed the url as well
        self.assertEqual(page.publisher_public.get_absolute_url(), other_url + "page/")
        self.assertEqual(child.publisher_public.get_absolute_url(), other_url + "page/child/")

    def test_publish_works_with_descendants(self):
        """
        For help understanding what this tests for, see:
        http://articles.sitepoint.com/print/hierarchical-data-database

        Creates this published structure:
                            home
                          /      \
                       item1   item2
                              /     \
                         subitem1 subitem2
        """
        home_page = create_page("home", "nav_playground.html", "en",
                                published=True, in_navigation=False)

        create_page("item1", "nav_playground.html", "en", parent=home_page,
                    published=True)
        item2 = create_page("item2", "nav_playground.html", "en", parent=home_page,
                            published=True)

        create_page("subitem1", "nav_playground.html", "en", parent=item2,
                    published=True)
        create_page("subitem2", "nav_playground.html", "en", parent=item2,
                    published=True)
        item2 = item2.reload()
        not_drafts = list(Page.objects.filter(publisher_is_draft=False).order_by('path'))
        drafts = list(Page.objects.filter(publisher_is_draft=True).order_by('path'))

        self.assertEqual(len(not_drafts), 5)
        self.assertEqual(len(drafts), 5)

        for idx, draft in enumerate(drafts):
            public = not_drafts[idx]
            # Check that a node doesn't become a root node magically
            self.assertEqual(bool(public.parent_id), bool(draft.parent_id))
            if public.parent:
                self.assertEqual(public.path[0:4], public.parent.path[0:4])
                self.assertTrue(public.parent in public.get_ancestors())
                self.assertTrue(public in public.parent.get_descendants())
                self.assertTrue(public in public.parent.get_children())
            if draft.parent:
                # Same principle for the draft tree
                self.assertEqual(draft.path[0:4], draft.parent.path[0:4])
                self.assertTrue(draft.parent in draft.get_ancestors())
                self.assertTrue(draft in draft.parent.get_descendants())
                self.assertTrue(draft in draft.parent.get_children())

        # Now call publish again. The structure should not change.
        item2.publish('en')

        not_drafts = list(Page.objects.filter(publisher_is_draft=False).order_by('path'))
        drafts = list(Page.objects.filter(publisher_is_draft=True).order_by('path'))

        self.assertEqual(len(not_drafts), 5)
        self.assertEqual(len(drafts), 5)

        for idx, draft in enumerate(drafts):
            public = not_drafts[idx]
            # Check that a node doesn't become a root node magically
            self.assertEqual(bool(public.parent_id), bool(draft.parent_id))
            self.assertEqual(public.numchild, draft.numchild)
            if public.parent:
                self.assertEqual(public.path[0:4], public.parent.path[0:4])
                self.assertTrue(public.parent in public.get_ancestors())
                self.assertTrue(public in public.parent.get_descendants())
                self.assertTrue(public in public.parent.get_children())
            if draft.parent:
                self.assertEqual(draft.path[0:4], draft.parent.path[0:4])
                self.assertTrue(draft.parent in draft.get_ancestors())
                self.assertTrue(draft in draft.parent.get_descendants())
                self.assertTrue(draft in draft.parent.get_children())

    def test_publish_with_pending_unpublished_descendants(self):
        # ref: https://github.com/divio/django-cms/issues/5900
        ancestor = self.create_page("Ancestor", published=False)
        parent = self.create_page("Child", published=False, parent=ancestor)
        child = self.create_page("Child", published=False, parent=parent)

        child.publish('en')
        self.assertEqual(
            child.reload().get_publisher_state("en"),
            PUBLISHER_STATE_PENDING
        )

        parent.publish('en')
        self.assertEqual(
            parent.reload().get_publisher_state("en"),
            PUBLISHER_STATE_PENDING
        )

        ancestor.publish('en')

        self.assertEqual(
            ancestor.reload().get_publisher_state("en"),
            PUBLISHER_STATE_DEFAULT
        )
        self.assertEqual(
            parent.reload().get_publisher_state("en"),
            PUBLISHER_STATE_DEFAULT
        )
        self.assertEqual(
            child.reload().get_publisher_state("en"),
            PUBLISHER_STATE_DEFAULT
        )
