# -*- coding: utf-8 -*-
from __future__ import with_statement
import copy
from cms.api import create_page, create_title, publish_page, add_plugin
from cms.models import Title
from cms.test_utils.testcases import (CMSTestCase, SettingsOverrideTestCase,
                                      URL_CMS_PAGE_ADD, 
                                      URL_CMS_PAGE, URL_CMS_PAGE_CHANGE,
                                      URL_CMS_PAGE_CHANGE_LANGUAGE)
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.mock import AttributeObject
from cms.utils import get_cms_setting
from cms.utils.conf import get_languages
from django.conf import settings
from django.contrib.sites.models import Site

from django.contrib.auth.models import User
from django.http import Http404, HttpResponseRedirect

TEMPLATE_NAME = 'tests/rendering/base.html'

def get_primary_lanaguage(current_site=None):
    """Fetch the first language of the current site settings."""
    current_site = current_site or Site.objects.get_current()
    return get_languages()[current_site.id][0]['code']    
    
def get_secondary_lanaguage(current_site=None):
    """Fetch the other language of the current site settings."""
    current_site = current_site or Site.objects.get_current()
    return get_languages()[current_site.id][1]['code']    

class MultilingualTestCase(SettingsOverrideTestCase):
    settings_overrides = {
        'CMS_TEMPLATES': [(TEMPLATE_NAME, TEMPLATE_NAME), ('extra_context.html', 'extra_context.html'),
                          ('nav_playground.html', 'nav_playground.html')],
    }


    def test_create_page(self):
        """
        Test that a page can be created
        and that a new language can be created afterwards in the admin pages
        """
        
        # Create a new page
        
        # Use the very first language in the list of languages
        # for the current site
        current_site = Site.objects.get_current()
        TESTLANG = get_primary_lanaguage(current_site=current_site)
        page_data = self.get_new_page_data_dbfields(
            site=current_site, 
            language=TESTLANG
        )

        page = create_page(**page_data)
        title = page.get_title_obj()
        
        # A title is set?
        self.assertNotEqual(title, None)
        
        # Publish and unpublish the page
        page.published = True
        page.save()
        page.published = False
        page.save()
        
        # Has correct title and slug after calling save()?
        self.assertEqual(page.get_title(), page_data['title'])
        self.assertEqual(page.get_slug(), page_data['slug'])
        self.assertEqual(page.placeholders.all().count(), 2)
        
        # Were public instances created?
        title = Title.objects.drafts().get(slug=page_data['slug'])
    
        # Test that it's the default language
        self.assertEqual(title.language, TESTLANG)
            
        # Do stuff using admin pages
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            
            page_data = self.get_pagedata_from_dbfields(page_data)
            
            # Publish page using the admin
            page_data['published'] = True
            response = self.client.post(URL_CMS_PAGE_CHANGE_LANGUAGE % (page.pk, TESTLANG),
                                        page_data)
            
            page = page.reload()
            self.assertTrue(page.published)
            
            # Create a different language using the edit admin page
            # This test case is bound in actual experience...
            # pull#1604
            page_data2 = page_data.copy()
            page_data2['title'] = 'ein Titel'
            page_data2['slug'] = 'ein-slug'
            TESTLANG2 = get_secondary_lanaguage(current_site=current_site)
            page_data2['language'] = TESTLANG2
            
            # Ensure that the language version is not returned
            # since it does not exist
            self.assertRaises(Title.DoesNotExist,
                              page.get_title_obj,
                              language=TESTLANG2, fallback=False)
            
            # Now create it
            response = self.client.post(URL_CMS_PAGE_CHANGE_LANGUAGE % (page.pk, TESTLANG2),
                                        page_data2)
            
            page = page.reload()
            
            # Test the new language version
            self.assertEqual(page.get_title(language=TESTLANG2), page_data2['title'])
            self.assertEqual(page.get_slug(language=TESTLANG2), page_data2['slug'])
            
            # Test the default language version (TESTLANG)
            self.assertEqual(page.get_slug(language=TESTLANG, fallback=False), page_data['slug'])
            self.assertEqual(page.get_title(language=TESTLANG, fallback=False), page_data['title'])
            self.assertEqual(page.get_slug(fallback=False), page_data['slug'])
            self.assertEqual(page.get_title(fallback=False), page_data['title'])
    
    
    def test_multilingual_page(self):
        TESTLANG = get_primary_lanaguage()
        TESTLANG2 = get_secondary_lanaguage()
        page = create_page("mlpage", "nav_playground.html", TESTLANG)
        create_title(TESTLANG2, page.get_title(), page, slug=page.get_slug())
        page.rescan_placeholders()
        page = self.reload(page)
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, "TextPlugin", TESTLANG2, body="test")
        add_plugin(placeholder, "TextPlugin", TESTLANG, body="test")
        self.assertEqual(placeholder.cmsplugin_set.filter(language=TESTLANG2).count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language=TESTLANG).count(), 1)
        user = User.objects.create_superuser('super', 'super@django-cms.org', 'super')
        page = publish_page(page, user)
        public = page.publisher_public
        placeholder = public.placeholders.all()[0]
        self.assertEqual(placeholder.cmsplugin_set.filter(language=TESTLANG2).count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language=TESTLANG).count(), 1)

    def test_frontend_lang(self):
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][0]['public'] = False
        with SettingsOverride(CMS_LANGUAGES=lang_settings, LANGUAGE_CODE="en"):
            page = create_page("page1", "nav_playground.html", "en")
            create_title("de", page.get_title(), page, slug=page.get_slug())
            page2 = create_page("page2", "nav_playground.html", "en")
            create_title("de", page2.get_title(), page2, slug=page2.get_slug())
            page3 = create_page("page2", "nav_playground.html", "en")
            create_title("de", page3.get_title(), page3, slug=page3.get_slug())
            page4 = create_page("page4", "nav_playground.html", "de")
            page.publish()
            page2.publish()
            page3.publish()
            page4.publish()
            response = self.client.get("/en/")
            self.assertRedirects(response, "/de/")
            response = self.client.get("/en/page2/")
            self.assertEqual(response.status_code, 404)
            response = self.client.get("/de/")
            self.assertEqual(response.status_code, 200)
            response = self.client.get("/de/page2/")
            self.assertEqual(response.status_code, 200)
            # check if the admin can see non-public langs
            admin = self.get_superuser()
            if self.client.login(username=admin.username, password="admin"):
                response = self.client.get("/en/page2/")
                self.assertEqual(response.status_code, 200)
                response = self.client.get("/en/page4/")
                self.assertEqual(response.status_code, 302)

    def test_detail_view_404_when_no_language_is_found(self):
        page = create_page("page1", "nav_playground.html", "en")
        create_title("de", page.get_title(), page, slug=page.get_slug())
        page.publish()

        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=[],
            CMS_LANGUAGES={
                1:[
                    {'code':'x-klingon', 'name':'Klingon','public':True, 'fallbacks':[]},
                    {'code':'x-elvish', 'name':'Elvish', 'public':True, 'fallbacks':[]},
               ]}):
            from cms.views import details
            request = AttributeObject(
                REQUEST={'language': 'x-elvish'},
                GET=[],
                session={},
                path='/',
                current_page=None,
                method='GET',
                COOKIES={},
                META={},
                user=User(),
            )
            self.assertRaises(Http404, details, request, '')

    def test_detail_view_fallback_language(self):
        '''
        Ask for a page in elvish (doesn't exist), and assert that it fallsback
        to English
        '''
        page = create_page("page1", "nav_playground.html", "en")
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=[],
            CMS_LANGUAGES={
                1:[
                    {'code':'x-klingon', 'name':'Klingon', 'public':True, 'fallbacks':[]},
                    {'code':'x-elvish', 'name':'Elvish', 'public':True, 'fallbacks':['x-klingon', 'en', ]},
                    ]},
            ):
            create_title("x-klingon", "futla ak", page, slug=page.get_slug())
            page.publish()
            from cms.views import details

            request = AttributeObject(
                REQUEST={'language': 'x-elvish'},
                GET=[],
                session={},
                path='/',
                current_page=None,
                method='GET',
                COOKIES={},
                META={},
                user=User(),
            )

            response = details(request, '')
            self.assertTrue(isinstance(response, HttpResponseRedirect))

    def test_language_fallback(self):
        """
        Test language fallbacks in details view
        """
        from cms.views import details
        p1 = create_page("page", "nav_playground.html", "en", published=True)
        request = self.get_request('/de/', 'de')
        response = details(request, p1.get_path())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/')
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][0]['fallbacks'] = []
        lang_settings[1][1]['fallbacks'] = []
        with SettingsOverride(CMS_LANGUAGES=lang_settings):
            response = self.client.get("/de/")
            self.assertEquals(response.status_code, 404)
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][0]['redirect_on_fallback'] = False
        lang_settings[1][1]['redirect_on_fallback'] = False
        with SettingsOverride(CMS_LANGUAGES=lang_settings):
            response = self.client.get("/de/")
            self.assertEquals(response.status_code, 200)
