# -*- coding: utf-8 -*-
from __future__ import with_statement
from django.contrib.auth.models import User
from django.core.management.base import CommandError
from django.core.urlresolvers import reverse

from cms.api import create_page, add_plugin
from cms.management.commands import publisher_publish
from cms.models import CMSPlugin
from cms.models.pagemodel import Page
from cms.test_utils.testcases import SettingsOverrideTestCase as TestCase
from cms.test_utils.util.context_managers import StdoutOverride


class PublisherCommandTests(TestCase):
    """
    Tests for the publish command
    """
    
    def test_command_line_should_raise_without_superuser(self):
        raised = False
        try:
            com = publisher_publish.Command()
            com.handle_noargs()
        except CommandError:
            raised = True
        self.assertTrue(raised)

    def test_command_line_publishes_zero_pages_on_empty_db(self):
        # we need to create a superuser (the db is empty)
        User.objects.create_superuser('djangocms', 'cms@example.com', '123456')
        
        pages_from_output = 0
        published_from_output = 0
        
        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            com = publisher_publish.Command()
            com.handle_noargs()
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work
            
        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])
                
        self.assertEqual(pages_from_output,0)
        self.assertEqual(published_from_output,0)

    def test_command_line_ignores_draft_page(self):
        # we need to create a superuser (the db is empty)
        User.objects.create_superuser('djangocms', 'cms@example.com', '123456')

        create_page("The page!", "nav_playground.html", "en", published=False)

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            com = publisher_publish.Command()
            com.handle_noargs()
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output,0)
        self.assertEqual(published_from_output,0)

        self.assertEqual(Page.objects.public().count(), 0)

    def test_command_line_publishes_one_page(self):
        """
        Publisher always creates two Page objects for every CMS page,
        one is_draft and one is_public.

        The public version of the page can be either published or not.

        This bit of code uses sometimes manager methods and sometimes manual
        filters on purpose (this helps test the managers)
        """
        # we need to create a superuser (the db is empty)
        User.objects.create_superuser('djangocms', 'cms@example.com', '123456')
        
        # Now, let's create a page. That actually creates 2 Page objects
        create_page("The page!", "nav_playground.html", "en", published=True)
        draft = Page.objects.drafts()[0]
        draft.reverse_id = 'a_test' # we have to change *something*
        draft.save()
        
        pages_from_output = 0
        published_from_output = 0
        
        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            com = publisher_publish.Command()
            com.handle_noargs()
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work
            
        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])
                
        self.assertEqual(pages_from_output,1)
        self.assertEqual(published_from_output,1)
        # Sanity check the database (we should have one draft and one public)
        not_drafts = len(Page.objects.filter(publisher_is_draft=False))
        drafts = len(Page.objects.filter(publisher_is_draft=True))
        self.assertEquals(not_drafts,1)
        self.assertEquals(drafts,1)
        
        # Now check that the non-draft has the attribute we set to the draft.
        non_draft = Page.objects.public()[0]
        self.assertEquals(non_draft.reverse_id, 'a_test')

class PublishingTests(TestCase):

    settings_overrides = {'CMS_SHOW_START_DATE': False,
                          'CMS_SHOW_END_DATE': False,
                          # Necessary to trigger an error
                          'USE_I18N': False}

    def create_page(self, title=None, **kwargs):
        return create_page(title or self._testMethodName,
                           "nav_playground.html", "en", **kwargs)

    def test_publish_single(self):
        name = self._testMethodName
        page = self.create_page(name, published=False)
        self.assertFalse(page.published)

        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published()
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectDoesNotExist(public, title_set__title=name)
        self.assertObjectDoesNotExist(published, title_set__title=name)

        page.publish()

        self.assertTrue(page.published)
        self.assertEqual(page.publisher_state, Page.PUBLISHER_STATE_DEFAULT)
        self.assertIsNotNone(page.publisher_public)
        self.assertTrue(page.publisher_public.published)

        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(public, title_set__title=name)
        self.assertObjectExist(published, title_set__title=name)

    def test_publish_child_first(self):
        parent = self.create_page('parent', published=False)
        child = self.create_page('child', published=False, parent=parent)
        self.assertFalse(parent.published)
        self.assertFalse(child.published)

        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published()

        for name in ('parent', 'child'):
            self.assertObjectExist(drafts, title_set__title=name)
            self.assertObjectDoesNotExist(public, title_set__title=name)
            self.assertObjectDoesNotExist(published, title_set__title=name)

        child.publish()

        self.assertTrue(child.published)
        self.assertEqual(child.publisher_state, Page.PUBLISHER_STATE_PENDING)
        self.assertIsNone(child.publisher_public)

        # Since we have no parent, the state is otherwise unchanged
        for name in ('parent', 'child'):
            self.assertObjectExist(drafts, title_set__title=name)
            self.assertObjectDoesNotExist(public, title_set__title=name)
            self.assertObjectDoesNotExist(published, title_set__title=name)

        parent.publish()

        # Cascade publish for all pending descendants
        for name in ('parent', 'child'):
            self.assertObjectExist(drafts, title_set__title=name)
            page = drafts.get(title_set__title=name)
            self.assertTrue(page.published, name)
            self.assertEqual(page.publisher_state, Page.PUBLISHER_STATE_DEFAULT, name)
            self.assertIsNotNone(page.publisher_public, name)
            self.assertTrue(page.publisher_public.published, name)

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
        self.assertTrue(pageA.published)
        self.assertTrue(pageB.published)
        self.assertTrue(not pageC.published)
        self.assertEqual(len(Page.objects.public().published()), 2)

        # Let's publish C now.
        pageC.publish()

        # Assert all are published
        self.assertTrue(pageA.published)
        self.assertTrue(pageB.published)
        self.assertTrue(pageC.published)
        self.assertEqual(len(Page.objects.public().published()), 3)

    def test_publish_ordering(self):
        page = self.create_page('parent', published=True)
        pageA = self.create_page('pageA', parent=page, published=True)
        pageC = self.create_page('pageC', parent=page, published=True)
        pageB = self.create_page('pageB', parent=page, published=True)
        pageB.move_page(pageA, 'right')
        pageB.publish()
        # pageC needs reload since B has swapped places with it
        pageC.reload().publish()
        pageA.publish()

        drafts = Page.objects.drafts().order_by('tree_id', 'lft')
        draft_titles = [(p.get_title('en'), p.lft, p.rght) for p in drafts]
        self.assertEquals([('parent', 1, 8),
                           ('pageA', 2, 3),
                           ('pageB', 4, 5),
                           ('pageC', 6, 7)], draft_titles)
        public = Page.objects.public().order_by('tree_id', 'lft')
        public_titles = [(p.get_title('en'), p.lft, p.rght) for p in public]
        self.assertEquals([('parent', 1, 8),
                           ('pageA', 2, 3),
                           ('pageB', 4, 5),
                           ('pageC', 6, 7)], public_titles)

        page.publish()

        drafts = Page.objects.drafts().order_by('tree_id', 'lft')
        draft_titles = [(p.get_title('en'), p.lft, p.rght) for p in drafts]
        self.assertEquals([('parent', 1, 8),
                           ('pageA', 2, 3),
                           ('pageB', 4, 5),
                           ('pageC', 6, 7)], draft_titles)
        public = Page.objects.public().order_by('tree_id', 'lft')
        public_titles = [(p.get_title('en'), p.lft, p.rght) for p in public]
        self.assertEquals([('parent', 1, 8),
                           ('pageA', 2, 3),
                           ('pageB', 4, 5),
                           ('pageC', 6, 7)], public_titles)


    def test_unpublish_unpublish(self):
        name = self._testMethodName
        page = self.create_page(name, published=True)
        drafts = Page.objects.drafts()
        published = Page.objects.public().published()
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(published, title_set__title=name)

        page.unpublish()
        self.assertFalse(page.published)
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectDoesNotExist(published, title_set__title=name)

        page.publish()
        self.assertTrue(page.published)
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(published, title_set__title=name)

    def test_modify_child_while_pending(self):
        home = self.create_page("Home", published=True, in_navigation=True)
        child = self.create_page("Child", published=True, parent=home,
                                 in_navigation=False)
        home.unpublish()
        child = self.reload(child)
        self.assertTrue(child.published)
        self.assertFalse(child.publisher_public.published)
        self.assertFalse(child.in_navigation)
        self.assertFalse(child.publisher_public.in_navigation)

        child.in_navigation = True
        child.save()
        child.publish()
        child = self.reload(child)

        self.assertTrue(child.published)
        self.assertFalse(child.publisher_public.published)
        self.assertTrue(child.in_navigation)
        self.assertTrue(child.publisher_public.in_navigation)
        self.assertEqual(child.publisher_state, Page.PUBLISHER_STATE_PENDING)

        home.publish()
        child = self.reload(child)
        self.assertTrue(child.publisher_public.published)
        self.assertTrue(child.publisher_public.in_navigation)
        self.assertEqual(child.publisher_state, Page.PUBLISHER_STATE_DEFAULT)

    def test_republish_with_descendants(self):
        home = self.create_page("Home", published=True)
        child = self.create_page("Child", published=True, parent=home)
        gc = self.create_page("GC", published=True, parent=child)

        home.unpublish()
        child = self.reload(child)
        gc = self.reload(gc)

        self.assertTrue(child.published)
        self.assertTrue(gc.published)
        self.assertFalse(child.publisher_public.published)
        self.assertFalse(gc.publisher_public.published)
        self.assertEqual(child.publisher_state, Page.PUBLISHER_STATE_PENDING)
        self.assertEqual(gc.publisher_state, Page.PUBLISHER_STATE_PENDING)

        home.publish()
        child = self.reload(child)
        gc = self.reload(gc)

        self.assertTrue(child.published)
        self.assertTrue(gc.published)
        self.assertTrue(child.publisher_public.published)
        self.assertTrue(gc.publisher_public.published)
        self.assertEqual(child.publisher_state, Page.PUBLISHER_STATE_DEFAULT)
        self.assertEqual(gc.publisher_state, Page.PUBLISHER_STATE_DEFAULT)

    def test_republish_with_dirty_children(self):
        home = self.create_page("Home", published=True)
        dirty1 = self.create_page("Dirty1", published=True, parent=home)
        dirty2 = self.create_page("Dirty2", published=True, parent=home)
        home = self.reload(home)

        dirty1.save()
        home.unpublish()
        dirty2.save()
        dirty1 = self.reload(dirty1)
        dirty2 = self.reload(dirty2)
        self.assertTrue(dirty1.published)
        self.assertTrue(dirty2.published)
        self.assertFalse(dirty1.publisher_public.published)
        self.assertFalse(dirty2.publisher_public.published)
        self.assertEqual(dirty1.publisher_state, Page.PUBLISHER_STATE_DIRTY)
        self.assertEqual(dirty2.publisher_state, Page.PUBLISHER_STATE_DIRTY)

        home = self.reload(home)
        home.publish()
        dirty1 = self.reload(dirty1)
        dirty2 = self.reload(dirty2)
        self.assertTrue(dirty1.published)
        self.assertTrue(dirty2.published)
        self.assertTrue(dirty1.publisher_public.published)
        self.assertTrue(dirty2.publisher_public.published)
        self.assertEqual(dirty1.publisher_state, Page.PUBLISHER_STATE_DIRTY)
        self.assertEqual(dirty2.publisher_state, Page.PUBLISHER_STATE_DIRTY)

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

        home.unpublish()
        unpub1 = self.reload(unpub1)
        unpub2.unpublish() # Just marks this as not published
        for page in (unpub1, unpub2):
            self.assertFalse(page.published)
            self.assertEqual(page.publisher_state, Page.PUBLISHER_STATE_DIRTY)
        self.assertIsNone(unpub1.publisher_public)
        self.assertIsNotNone(unpub2.publisher_public)
        self.assertFalse(unpub2.publisher_public.published)

        gc1 = self.reload(gc1)
        gc2 = self.reload(gc2)
        for page in (gc1, gc2):
            self.assertTrue(page.published)
            self.assertEqual(page.publisher_state, Page.PUBLISHER_STATE_PENDING)
        self.assertIsNone(gc1.publisher_public)
        self.assertIsNotNone(gc2.publisher_public)
        self.assertFalse(gc2.publisher_public.published)

    def test_unpublish_with_descendants(self):
        page = self.create_page("Page", published=True)
        child = self.create_page("Child", parent=page, published=True)
        self.create_page("Grandchild", parent=child, published=True)
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published()

        self.assertEqual(page.get_descendant_count(), 2)
        base = reverse('pages-root')

        for url in (base, base + 'child/', base + 'child/grandchild/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        for title in ('Page', 'Child', 'Grandchild'):
            self.assertObjectExist(drafts, title_set__title=title)
            self.assertObjectExist(public, title_set__title=title)
            self.assertObjectExist(published, title_set__title=title)
            item = drafts.get(title_set__title=title)
            self.assertTrue(item.published)
            self.assertEqual(item.publisher_state, Page.PUBLISHER_STATE_DEFAULT)

        self.assertTrue(page.unpublish(), 'Unpublish was not successful')
        self.assertFalse(page.published)
        for url in (base, base + 'child/', base + 'child/grandchild/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

        for title in ('Page', 'Child', 'Grandchild'):
            self.assertObjectExist(drafts, title_set__title=title)
            self.assertObjectExist(public, title_set__title=title)
            self.assertObjectDoesNotExist(published, title_set__title=title)
            item = drafts.get(title_set__title=title)
            if title == 'Page':
                self.assertFalse(item.published)
                self.assertFalse(item.publisher_public.published)
                # Not sure what the proper state of these are after unpublish
                #self.assertEqual(page.publisher_state, Page.PUBLISHER_STATE_DEFAULT)
                self.assertTrue(page.is_dirty())
            else:
                # The changes to the published subpages are simply that the
                # published flag of the PUBLIC instance goes to false, and the
                # publisher state is set to mark waiting for parent
                self.assertTrue(item.published, title)
                self.assertFalse(item.publisher_public.published, title)
                self.assertEqual(item.publisher_state, Page.PUBLISHER_STATE_PENDING,
                                 title)
                self.assertFalse(item.is_dirty(), title)

    def test_unpublish_with_dirty_descendants(self):
        page = self.create_page("Page", published=True)
        child = self.create_page("Child", parent=page, published=True)
        gchild = self.create_page("Grandchild", parent=child, published=True)
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published()
        child.save()

        self.assertTrue(child.is_dirty())
        self.assertFalse(gchild.is_dirty())
        self.assertTrue(child.publisher_public.published)
        self.assertTrue(gchild.publisher_public.published)

        page.unpublish()
        child = self.reload(child)
        gchild = self.reload(gchild)
        # Descendants keep their dirty status after unpublish
        self.assertTrue(child.is_dirty())
        self.assertFalse(gchild.is_dirty())
        # However, their public version is still removed no matter what
        self.assertFalse(child.publisher_public.published)
        self.assertFalse(gchild.publisher_public.published)

    def test_republish_multiple_root(self):
        # TODO: The paths do not match expected behaviour
        home = self.create_page("Page", published=True)
        other = self.create_page("Another Page", published=True)
        child = self.create_page("Child", published=True, parent=home)
        child2 = self.create_page("Child", published=True, parent=other)
        self.assertTrue(home.is_home())
        self.assertTrue(home.publisher_public.is_home())
        root = reverse('pages-root')
        self.assertEqual(home.get_absolute_url(), root)
        self.assertEqual(home.get_public_object().get_absolute_url(), root)
        self.assertEqual(child.get_absolute_url(), root+'child/')
        self.assertEqual(child.get_public_object().get_absolute_url(), root+'child/')
        self.assertEqual(other.get_absolute_url(), root+'another-page/')
        self.assertEqual(other.get_public_object().get_absolute_url(), root+'another-page/')
        self.assertEqual(child2.get_absolute_url(), root+'another-page/child/')
        self.assertEqual(child2.get_public_object().get_absolute_url(), root+'another-page/child/')

        home.unpublish()
        home = self.reload(home)
        other = self.reload(other)
        child = self.reload(child)
        child2 = self.reload(child2)
        self.assertFalse(home.is_home())
        self.assertFalse(home.publisher_public.is_home())
        self.assertTrue(other.is_home())
        self.assertTrue(other.publisher_public.is_home())

        self.assertEqual(other.get_absolute_url(), root)
        self.assertEqual(other.get_public_object().get_absolute_url(), root)
        self.assertEqual(home.get_absolute_url(), root+'page/')
        self.assertEqual(home.get_public_object().get_absolute_url(), root+'page/')
        # TODO: These assertions are failing
        #self.assertEqual(child.get_absolute_url(), root+'page/child/')
        #self.assertEqual(child.get_public_object().get_absolute_url(), root+'page/child/')
        #self.assertEqual(child2.get_absolute_url(), root+'child/')
        #self.assertEqual(child2.get_public_object().get_absolute_url(), root+'child/')

        home.publish()
        home = self.reload(home)
        other = self.reload(other)
        child = self.reload(child)
        child2 = self.reload(child2)
        self.assertTrue(home.is_home())
        self.assertTrue(home.publisher_public.is_home())
        self.assertEqual(home.get_absolute_url(), root)
        self.assertEqual(home.get_public_object().get_absolute_url(), root)
        self.assertEqual(child.get_absolute_url(), root+'child/')
        self.assertEqual(child.get_public_object().get_absolute_url(), root+'child/')
        self.assertEqual(other.get_absolute_url(), root+'another-page/')
        self.assertEqual(other.get_public_object().get_absolute_url(), root+'another-page/')
        self.assertEqual(child2.get_absolute_url(), root+'another-page/child/')
        self.assertEqual(child2.get_public_object().get_absolute_url(), root+'another-page/child/')

    def test_revert_contents(self):
        user = self.get_superuser()
        page = create_page("Page", "nav_playground.html", "en", published=True,
                           created_by=user)
        placeholder = page.placeholders.get(slot=u"body")
        deleted_plugin = add_plugin(placeholder, u"TextPlugin", u"en", body="Deleted content")
        text_plugin = add_plugin(placeholder, u"TextPlugin", u"en", body="Public content")
        page.publish()

        # Modify and delete plugins
        text_plugin.body = "<p>Draft content</p>"
        text_plugin.save()
        deleted_plugin.delete()
        self.assertEquals(CMSPlugin.objects.count(), 3)

        # Now let's revert and restore
        page.revert()
        self.assertEquals(page.publisher_state, Page.PUBLISHER_STATE_DEFAULT)
        self.assertEquals(page.pagemoderatorstate_set.count(), 0)

        self.assertEquals(CMSPlugin.objects.count(), 4)
        plugins = CMSPlugin.objects.filter(placeholder__page=page)
        self.assertEquals(plugins.count(), 2)

        plugins = [plugin.get_plugin_instance()[0] for plugin in plugins]
        self.assertEquals(plugins[0].body, "Deleted content")
        self.assertEquals(plugins[1].body, "Public content")

    def test_revert_move(self):
        parent = create_page("Parent", "nav_playground.html", "en", published=True)
        parent_url = parent.get_absolute_url()
        page = create_page("Page", "nav_playground.html", "en", published=True,
                           parent=parent)
        other = create_page("Other", "nav_playground.html", "en", published=True)
        other_url = other.get_absolute_url()

        child = create_page("Child", "nav_playground.html", "en", published=True,
                            parent=page)
        self.assertEqual(page.get_absolute_url(), parent_url + "page/")
        self.assertEqual(child.get_absolute_url(), parent_url + "page/child/")

        # Now let's move it (and the child)
        page.move_page(other)
        page = self.reload(page)
        child = self.reload(child)
        self.assertEqual(page.get_absolute_url(), other_url + "page/")
        self.assertEqual(child.get_absolute_url(), other_url + "page/child/")
        # Public version is still in the same url
        self.assertEqual(page.publisher_public.get_absolute_url(), parent_url + "page/")
        self.assertEqual(child.publisher_public.get_absolute_url(), parent_url + "page/child/")

        # Use revert to bring things back to normal
        page.revert()
        page = self.reload(page)
        child = self.reload(child)
        self.assertEqual(page.get_absolute_url(), other_url + "page/")
        self.assertEqual(child.get_absolute_url(), other_url + "page/child/")

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
            
        not_drafts = list(Page.objects.filter(publisher_is_draft=False).order_by('lft'))
        drafts = list(Page.objects.filter(publisher_is_draft=True).order_by('lft'))
        
        self.assertEquals(len(not_drafts), 5)
        self.assertEquals(len(drafts), 5)

        for idx, draft in enumerate(drafts):
            public = not_drafts[idx]
            # Check that a node doesn't become a root node magically
            self.assertEqual(bool(public.parent_id), bool(draft.parent_id))
            if public.parent :
                # Let's assert the MPTT tree is consistent
                self.assertTrue(public.lft > public.parent.lft)
                self.assertTrue(public.rght < public.parent.rght)
                self.assertEquals(public.tree_id, public.parent.tree_id)
                self.assertTrue(public.parent in public.get_ancestors())
                self.assertTrue(public in public.parent.get_descendants())
                self.assertTrue(public in public.parent.get_children())
            if draft.parent:
                # Same principle for the draft tree
                self.assertTrue(draft.lft > draft.parent.lft)
                self.assertTrue(draft.rght < draft.parent.rght)
                self.assertEquals(draft.tree_id, draft.parent.tree_id)
                self.assertTrue(draft.parent in draft.get_ancestors())
                self.assertTrue(draft in draft.parent.get_descendants())
                self.assertTrue(draft in draft.parent.get_children())

        # Now call publish again. The structure should not change.
        item2.publish()
            
        not_drafts = list(Page.objects.filter(publisher_is_draft=False).order_by('lft'))
        drafts = list(Page.objects.filter(publisher_is_draft=True).order_by('lft'))
        
        self.assertEquals(len(not_drafts), 5)
        self.assertEquals(len(drafts), 5)

        for idx, draft in enumerate(drafts):
            public = not_drafts[idx]
            # Check that a node doesn't become a root node magically
            self.assertEqual(bool(public.parent_id), bool(draft.parent_id))
            if public.parent :
                # Let's assert the MPTT tree is consistent
                self.assertTrue(public.lft > public.parent.lft)
                self.assertTrue(public.rght < public.parent.rght)
                self.assertEquals(public.tree_id, public.parent.tree_id)
                self.assertTrue(public.parent in public.get_ancestors())
                self.assertTrue(public in public.parent.get_descendants())
                self.assertTrue(public in public.parent.get_children())
            if draft.parent:
                # Same principle for the draft tree
                self.assertTrue(draft.lft > draft.parent.lft)
                self.assertTrue(draft.rght < draft.parent.rght)
                self.assertEquals(draft.tree_id, draft.parent.tree_id)
                self.assertTrue(draft.parent in draft.get_ancestors())
                self.assertTrue(draft in draft.parent.get_descendants())
                self.assertTrue(draft in draft.parent.get_children())

