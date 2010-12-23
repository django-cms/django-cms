'''
Created on Dec 23, 2010

@author: Christopher Glass <christopher.glass@divio.ch>
'''
from cms.management.commands import publisher_publish
from cms.models.pagemodel import Page
from cms.tests.base import CMSTestCase
from cms.tests.util.settings_contextmanager import SettingsOverride
from cms.tests.util.standard_out_contextmanager import StdoutOverride
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
        pageA = self.new_create_page(title="Page A", published= True, 
                                     in_navigation= True)
        pageB = self.new_create_page(parent_page=pageA,title="Page B", 
                                     published= True, in_navigation= True)
        pageC = self.new_create_page(parent_page=pageA,title="Page C", 
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
        
#    def test_05_command_line_publishes_one_page(self):
#        # we need to create a superuser (the db is empty)
#        User.objects.create_superuser('djangocms', 'cms@example.com', '123456')
#        
#        # Now, let's create an unpublished page.
#        page = self.new_create_page(title="I'm unpublished", published= False)
#        pages_from_output = 0
#        published_from_output = 0
#        
#        with StdoutOverride() as buffer:
#            # Now we don't expect it to raise, but we need to redirect IO
#            com = publisher_publish.Command()
#            com.handle_noargs()
#            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work
#            
#        for line in lines:
#            import ipdb
#            if 'Total' in line:
#                ipdb.set_trace()
#                pages_from_output = int(line.split(':')[1])
#            elif 'Published' in line:
#                ipdb.set_trace()
#                published_from_output = int(line.split(':')[1])
#                
#        self.assertEqual(pages_from_output,1)
#        self.assertEqual(published_from_output,1)
