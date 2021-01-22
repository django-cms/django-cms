# -*- coding: utf-8 -*-
from cms.api import create_page, create_title, publish_pages
from cms.test_utils.testcases import (CMSTestCase)


class TitlePathTestCase(CMSTestCase):

    def test0001_translated_subpage_title_path(self):
        """
        Test the path when parent page is created after child translation 
        """

        p_1 = create_page('en-1', "nav_playground.html", 'en',
                          slug = 'en-1', published=True)
        p_1_1 = create_page('en-1-1', "nav_playground.html", 'en',
                            slug = 'en-1-1', parent=p_1, published=True)

        create_title('de', 'de-1-1', p_1_1, slug='de-1-1')

        # Parent 'de' title created after de-1-1 translation
        create_title('de', 'de-1', p_1, slug='de-1')

        p_1.publish('de')
        p_1_1.publish('de')

        response = self.client.get('/de/de-1/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/de/en-1/de-1-1/')
        if response.status_code == 200:
            print('\n********** Unexpected response 200 for /de/en-1/de-1-1/')
        response = self.client.get('/de/de-1/de-1-1/')
        self.assertEqual(response.status_code, 200)
        

    def test0002_changed_parent_slug(self):    
        """
        Test the child path when parent page slug is changed
        """
        
        p_1 = create_page('BadFoo', "nav_playground.html", 'en',
                          slug = 'badfoo', published=True)
        p_1_1 = create_page('Bar', "nav_playground.html", 'en',
                            slug = 'bar', parent=p_1, published=True)
        t_1 = p_1.get_title_obj(language='en', fallback=False)
        t_1.title='Foo'
        t_1.path='foo'
        t_1.save()

        p_1.publish('en')
        p_1_1.publish('en')

        response = self.client.get('/en/foo/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/en/badfoo/bar/')
        if response.status_code == 200:
            print('\n********** Unexpected response 200 for /en/badfoo/bar/')
        response = self.client.get('/en/foo/bar/')
        self.assertEqual(response.status_code, 200)

        
