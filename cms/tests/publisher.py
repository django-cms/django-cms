# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page
from cms.management.commands import publisher_publish
from cms.models.pagemodel import Page
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import (SettingsOverride, 
    StdoutOverride)
from django.contrib.auth.models import User
from django.core.management.base import CommandError

class PublisherTestCase(CMSTestCase):
    '''
    A test case to exercise publisher
    '''
    
    def test_simple_publisher(self):
        '''
        Creates the stuff needed for theses tests.
        Please keep this up-to-date (the docstring!)
                
                A
               / \
              B  C
        '''
        # Create a simple tree of 3 pages
        pageA = create_page("Page A", "nav_playground.html", "en",
                            published= True, in_navigation= True)
        pageB = create_page("Page B", "nav_playground.html", "en", 
                            parent=pageA, published=True, in_navigation=True)
        pageC = create_page("Page C", "nav_playground.html", "en",
                            parent=pageA, published=False, in_navigation=True)
        # Assert A and B are published, C unpublished
        self.assertTrue(pageA.published)
        self.assertTrue(pageB.published)
        self.assertTrue(not pageC.published)
        self.assertTrue(len(Page.objects.published()), 2)
        
        # Let's publish C now.
        pageC.publish()
        
        # Assert A and B are published, C unpublished
        self.assertTrue(pageA.published)
        self.assertTrue(pageB.published)
        self.assertTrue(pageC.published)
        self.assertTrue(len(Page.objects.published()), 3)
        
    def test_command_line_should_raise_without_superuser(self):
        raised = False
        try:
            com = publisher_publish.Command()
            com.handle_noargs()
        except CommandError:
            raised = True
        self.assertTrue(raised)
        
    def test_command_line_should_raise_when_moderator_false(self):
        with SettingsOverride(CMS_MODERATOR=False):
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
        
    def test_command_line_publishes_one_page(self):
        '''
        Publisher always creates two Page objects for every CMS page,
        one is_draft and one is_public.
        
        The public version of the page can be either published or not.
        
        This bit of code uses sometimes manager methods and sometimes manual
        filters on purpose (this helps test the managers)
        '''
        # we need to create a superuser (the db is empty)
        User.objects.create_superuser('djangocms', 'cms@example.com', '123456')
        
        # Now, let's create a page. That actually creates 2 Page objects
        create_page("The page!", "nav_playground.html", "en", published=True, 
                    in_navigation=True)
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
        
    def test_unpublish(self):
        page = create_page("Page", "nav_playground.html", "en", published=True,
                           in_navigation=True)
        page.published = False
        page.save()
        self.assertEqual(page.published, False)
        page.published = True
        page.save()
        self.assertEqual(page.published, True)

    def test_publish_works_with_descendants(self):
        '''
        For help understanding what this tests for, see:
        http://articles.sitepoint.com/print/hierarchical-data-database
        '''
        home_page = create_page("home", "nav_playground.html", "en",
                                published=True, in_navigation=False)
            
        create_page("item1", "nav_playground.html", "en", parent=home_page,
                    published=True)
        item2 = create_page("item2", "nav_playground.html", "en", parent=home_page,
                            published=True)
            
        item2 = self.reload_page(item2)    

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

            
        item2 = self.reload_page(item2)    
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
