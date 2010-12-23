'''
Created on Dec 23, 2010

@author: Christopher Glass <christopher.glass@divio.ch>
'''
from cms.management.commands import publisher_publish
from cms.models.pagemodel import Page
from cms.tests.base import CMSTestCase
from cms.tests.util.settings_contextmanager import SettingsOverride
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
        # Nuke all pages.
        #Page.objects.all().delete()
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