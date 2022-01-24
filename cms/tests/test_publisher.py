from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse
from django.utils.translation import override as force_language
from djangocms_text_ckeditor.models import Text

from cms.api import add_plugin, create_page, create_title
from cms.constants import (
    PUBLISHER_STATE_DEFAULT, PUBLISHER_STATE_DIRTY, PUBLISHER_STATE_PENDING,
)
from cms.management.commands.subcommands.publisher_publish import (
    PublishCommand,
)
from cms.models import CMSPlugin, Page, Title, TreeNode
from cms.plugin_pool import plugin_pool
from cms.test_utils.testcases import CMSTestCase as TestCase
from cms.test_utils.util.context_managers import StdoutOverride
from cms.test_utils.util.fuzzy_int import FuzzyInt
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
            lines = buffer.getvalue().split('\n')  # NB: readlines() doesn't work

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
            lines = buffer.getvalue().split('\n')  # NB: readlines() doesn't work

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
            lines = buffer.getvalue().split('\n')  # NB: readlines() doesn't work

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
            lines = buffer.getvalue().split('\n')  # NB: readlines() doesn't work

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
            lines = buffer.getvalue().split('\n')  # NB: readlines() doesn't work

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
        add_plugin(
            draft.placeholders.get(slot="body"),
            "TextPlugin", "en", body="Test content"
        )
        draft.publish('en')
        add_plugin(
            draft.placeholders.get(slot="body"),
            "TextPlugin", "en", body="Test content"
        )

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
            lines = buffer.getvalue().split('\n')  # NB: readlines() doesn't work

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
        page = create_page("The page!", "nav_playground.html", "en", published=False)
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
        create_page("example.com homepage", "nav_playground.html", "en", published=True)
        #a.example.com
        create_page("a.example.com homepage", "nav_playground.html", "de", site=siteA, published=True)
        #b.example.com
        create_page("b.example.com homepage", "nav_playground.html", "de", site=siteB, published=True)
        create_page("b.example.com about", "nav_playground.html", "nl", site=siteB, published=True)

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            call_command('cms', 'publisher-publish', site=siteB.id)
            lines = buffer.getvalue().split('\n')  # NB: readlines() doesn't work

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
            lines = buffer.getvalue().split('\n')  # NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 1)
        self.assertEqual(published_from_output, 1)


class PublishingTests(TestCase):

    def create_page(self, title=None, **kwargs):
        return create_page(title or self._testMethodName,
                           "nav_playground.html", "en", **kwargs)

    def test_publish_single(self):
        name = self._testMethodName
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        page = self.create_page(name, published=False)
        create_title('de', 'de-page', page)
        create_title('fr', 'fr-page', page)

        self.assertNeverPublished(page)
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectDoesNotExist(public, title_set__title=name)
        self.assertObjectDoesNotExist(public.published(language="en"), title_set__title=name)

        page.publish("en")

        self.assertPublished(page.reload())
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(public, title_set__title=name)
        self.assertFalse(public.published(language="de").exists())
        self.assertFalse(public.published(language="fr").exists())
        self.assertSequenceEqual(page.publisher_public.get_languages(), ['en'])

    def test_publish_admin(self):
        name = 'test_admin'
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        page = self.create_page(name, published=False)
        create_title('de', 'de-page', page)
        create_title('fr', 'fr-page', page)

        self.assertNeverPublished(page)
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectDoesNotExist(public, title_set__title=name)
        self.assertObjectDoesNotExist(public.published(language="en"), title_set__title=name)

        with self.login_user_context(self.get_superuser()):
            response = self.client.post(admin_reverse("cms_page_publish_page", args=[page.pk, 'en']))
            self.assertEqual(response.status_code, 302)

        page = page.reload()
        self.assertPublished(page)
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(public, title_set__title=name)
        self.assertFalse(public.published(language="de").exists())
        self.assertFalse(public.published(language="fr").exists())
        self.assertSequenceEqual(page.publisher_public.get_languages(), ['en'])

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
        child = self.create_page('child', published=True)
        child.move_page(parent.node, 'last-child')
        drafts = Page.objects.drafts()
        public = Page.objects.public()

        self.assertPending(child.reload())
        self.assertNeverPublished(parent.reload())

        self.assertObjectExist(drafts, title_set__title='parent')
        self.assertObjectDoesNotExist(public, title_set__title='parent')
        self.assertObjectDoesNotExist(public.published(language='en'), title_set__title='parent')

        self.assertObjectExist(drafts, title_set__title='child')
        self.assertObjectExist(public, title_set__title='child')
        self.assertObjectDoesNotExist(public.published(language='en'), title_set__title='child')

        parent.reload().publish("en")

        # Cascade publish for all pending descendants
        for name in ('parent', 'child'):
            page = drafts.get(title_set__title=name)
            self.assertPublished(page)
            self.assertObjectExist(drafts, title_set__title=name)
            self.assertObjectExist(public, title_set__title=name)
            self.assertObjectExist(public.published(language='en'), title_set__title=name)

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
        self.assertEqual(len(Page.objects.public().published(language="en")), 2)

        # Let's publish C now.
        pageC.publish("en")

        # Assert all are published
        self.assertTrue(pageA.publisher_public_id)
        self.assertTrue(pageB.publisher_public_id)
        self.assertTrue(pageC.publisher_public_id)
        self.assertEqual(len(Page.objects.public().published(language="en")), 3)

    def test_i18n_publishing(self):
        page = self.create_page('parent', published=True)
        self.assertEqual(Title.objects.all().count(), 2)
        create_title("de", "vater", page)
        self.assertEqual(Title.objects.all().count(), 3)
        self.assertEqual(Title.objects.filter(published=True).count(), 2)
        page.publish('de')
        self.assertEqual(Title.objects.all().count(), 4)
        self.assertEqual(Title.objects.filter(published=True).count(), 4)

    def test_unpublish_unpublish(self):
        name = self._testMethodName
        page = self.create_page(name, published=True)
        drafts = Page.objects.drafts()
        published = Page.objects.public().published(language="en")
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
        self.assertPublished(page)
        self.assertPublished(sub_page)
        page.reload().delete_translations()
        self.assertPending(sub_page.reload())

    def test_modify_child_while_pending(self):
        home = self.create_page("Home", published=True, in_navigation=True)
        child = self.create_page("Child", published=True, parent=home,
                                 in_navigation=False)
        home.reload().unpublish('en')

        self.assertPending(child.reload())

        child.refresh_from_db()
        child.in_navigation = True
        child.save()

        # assert draft dirty
        self.assertTrue(child.is_published('en'))
        self.assertTrue(child.get_title_obj('en').published)
        self.assertEqual(child.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)

        # assert public is still unpublished
        self.assertPending(child.publisher_public.reload())

        home.reload().publish('en')

        # assert draft still dirty
        self.assertTrue(child.is_published('en'))
        self.assertTrue(child.get_title_obj('en').published)
        self.assertEqual(child.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)

        # assert public is published
        self.assertPublished(child.publisher_public.reload())

    def test_republish_with_descendants(self):
        home = self.create_page("Home", published=True)
        child = self.create_page("Child", published=True, parent=home)
        grand_child = self.create_page("GC", published=True, parent=child)

        # control
        self.assertPublished(child)
        self.assertPublished(grand_child)

        home.reload().unpublish('en')
        self.assertPending(child.reload())
        self.assertPending(grand_child.reload())

        home.reload().publish('en')
        self.assertPublished(child.reload())
        self.assertPublished(grand_child.reload())

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
        dirty2 = self.reload(dirty2)
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

        self.assertNeverPublished(unpub1)
        self.assertNeverPublished(gc1)
        self.assertPublished(unpub2)
        self.assertPublished(gc2)

        # Un-publish root page
        home.reload().unpublish('en')

        unpub1 = self.reload(unpub1)
        unpub2 = self.reload(unpub2)
        unpub2.unpublish('en')  # Just marks this as not published

        self.assertNeverPublished(unpub1)
        self.assertNeverPublished(gc1)
        self.assertUnpublished(unpub2.reload())
        self.assertPending(gc2.reload())

    def test_unpublish_with_descendants(self):
        page = self.create_homepage("Page", "nav_playground.html", "en", published=True)
        child = self.create_page("Child", parent=page, published=True)
        self.create_page("Grandchild", parent=child, published=True)
        page = page.reload()
        child.reload()
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        self.assertEqual(public.published(language="en").count(), 3)
        self.assertEqual(page.node.get_descendant_count(), 2)
        base = reverse('pages-root')

        for url in (base, base + 'child/', base + 'child/grandchild/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

        for title in ('Page', 'Child', 'Grandchild'):
            self.assertObjectExist(drafts, title_set__title=title)
            self.assertObjectExist(public, title_set__title=title)
            self.assertObjectExist(public.published(language="en"), title_set__title=title)
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
            self.assertObjectDoesNotExist(public.published(language="en"), title_set__title=title)
            item = drafts.get(title_set__title=title)
            if title == 'Page':
                self.assertFalse(item.is_published("en"))
                self.assertFalse(item.publisher_public.is_published("en"))
                self.assertTrue(page.is_dirty('en'))
            else:
                # The changes to the published subpages are simply that the
                # published flag of the PUBLIC instance goes to false, and the
                # publisher state is set to mark waiting for parent
                self.assertFalse(item.is_published('en'), title)
                self.assertTrue(item.get_title_obj('en').published, title)
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
        child_1_1.move_page(target_node=child_1.node, position='first-child')

        # Assert "Child" page is not published (we never published it)
        self.assertNeverPublished(child_1)
        self.assertNeverPublished(child_1_2)

        # Assert "first child" is in pending state because
        # it's parent the "Child" page is not published.
        self.assertPending(child_1_1)

        # Publish "Child page"
        child_1.reload().publish('en')
        # Publish "second child"
        child_1_2.reload().publish('en')

        self.assertPublished(child_1.reload())
        self.assertPublished(child_1_2.reload())
        # Assert "first child" is no longer in pending state
        # and instead is in published state.
        self.assertPublished(child_1_1.reload())

        tree = (
            (page, '0001'),
            (child_1, '00010001'),
            (child_1_1, '000100010001'),
            (child_1_2, '000100010002'),
        )

        for page, path in tree:
            self.assertEqual(self.reload(page.node).path, path)

    def test_republish_multiple_root(self):
        # TODO: The paths do not match expected behaviour
        home = self.create_homepage("Page", "nav_playground.html", "en", published=True)
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
        other.reload().set_as_homepage()

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
        self.assertEqual(child2.get_absolute_url(), root + 'child/')
        self.assertEqual(child2.get_public_object().get_absolute_url(), root + 'child/')

        self.assertEqual(home.get_absolute_url(), root + 'page/')
        self.assertEqual(home.get_public_object().get_absolute_url(), root + 'page/')
        self.assertEqual(child.get_absolute_url(), root + 'page/child/')
        self.assertEqual(child.get_public_object().get_absolute_url(), root + 'page/child/')

        home.publish('en')
        home.set_as_homepage()
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
        placeholder = page.placeholders.get(slot="body")
        deleted_plugin = add_plugin(placeholder, "TextPlugin", "en", body="Deleted content")
        text_plugin = add_plugin(placeholder, "TextPlugin", "en", body="Public content")
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
        page = create_page(
            "Page", "nav_playground.html", "en",
            published=True, parent=parent
        )
        other = create_page("Other", "nav_playground.html", "en", published=True)
        other_url = other.get_absolute_url()

        child = create_page(
            "Child", "nav_playground.html", "en",
            published=True, parent=page
        )
        parent = parent.reload()
        page = page.reload()
        self.assertEqual(page.get_absolute_url(), parent_url + "page/")
        self.assertEqual(child.get_absolute_url(), parent_url + "page/child/")

        # Now let's move it (and the child)
        page.move_page(other.node)
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
        home_page = create_page(
            "home", "nav_playground.html", "en",
            published=True, in_navigation=False
        )

        create_page(
            "item1", "nav_playground.html", "en",
            parent=home_page, published=True
        )
        item2 = create_page(
            "item2", "nav_playground.html", "en",
            parent=home_page, published=True
        )

        create_page(
            "subitem1", "nav_playground.html", "en",
            parent=item2, published=True
        )
        create_page(
            "subitem2", "nav_playground.html", "en",
            parent=item2, published=True
        )
        item2 = item2.reload()

        self.assertEqual(Page.objects.filter(publisher_is_draft=False).count(), 5)
        self.assertEqual(TreeNode.objects.count(), 5)

        child_nodes = list(TreeNode.objects.filter(parent__isnull=False))

        for idx, node in enumerate(child_nodes):
            self.assertEqual(node.path[0:4], node.parent.path[0:4])
            self.assertTrue(node.parent in node.get_ancestors())
            self.assertTrue(node in node.parent.get_descendants())
            self.assertTrue(node in node.parent.get_children())

        # Now call publish again. The structure should not change.
        item2.publish('en')

        self.assertEqual(Page.objects.filter(publisher_is_draft=False).count(), 5)
        self.assertEqual(TreeNode.objects.count(), 5)

        child_nodes = list(TreeNode.objects.filter(parent__isnull=False))

        for idx, node in enumerate(child_nodes):
            self.assertEqual(node.path[0:4], node.parent.path[0:4])
            self.assertTrue(node.parent in node.get_ancestors())
            self.assertTrue(node in node.parent.get_descendants())
            self.assertTrue(node in node.parent.get_children())
