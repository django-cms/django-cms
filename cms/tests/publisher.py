'''
Created on Dec 23, 2010

@author: Christopher Glass <christopher.glass@divio.ch>
'''
from __future__ import with_statement
from cms.management.commands import publisher_publish
from cms.models.pagemodel import Page
from cms.tests.base import CMSTestCase
from cms.tests.util.context_managers import SettingsOverride, StdoutOverride
from django.contrib.auth.models import User
from django.core.management.base import CommandError

class PublisherTestCase(CMSTestCase):
    '''
    A test case to exercise publisher
    '''
    
    def test_01_simple_publisher(self):
        '''
        Creates the stuff needed for theses tests.
        Please keep this up-to-date (the docstring!)
                
                A
               / \
              B  C
        '''
        # Create a simple tree of 3 pages
        pageA = self.create_page(title="Page A", published= True, 
                                     in_navigation= True)
        pageB = self.create_page(parent_page=pageA,title="Page B", 
                                     published= True, in_navigation= True)
        pageC = self.create_page(parent_page=pageA,title="Page C", 
                                     published= False, in_navigation= True)
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
        
    def test_02_command_line_should_raise_without_superuser(self):
        raised = False
        try:
            com = publisher_publish.Command()
            com.handle_noargs()
        except CommandError:
            raised = True
        self.assertTrue(raised)
        
    def test_03_command_line_should_raise_when_moderator_false(self):
        with SettingsOverride(CMS_MODERATOR=False):
            raised = False
            try:
                com = publisher_publish.Command()
                com.handle_noargs()
            except CommandError:
                raised = True
        self.assertTrue(raised)
        
    def test_04_command_line_publishes_zero_pages_on_empty_db(self):
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
        
    def test_05_command_line_publishes_one_page(self):
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
        self.create_page(title="The page!", published=True, 
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
        
    def test_06_unpublish(self):
        page = self.create_page(title="Page", published=True,
                                    in_navigation=True)
        page.published = False
        page.save()
        self.assertEqual(page.published, False)
        page.published = True
        page.save()
        self.assertEqual(page.published, True)
