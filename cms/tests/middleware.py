#-*- coding: utf-8 -*-
from __future__ import with_statement
from cms.middleware.multilingual import MultilingualURLMiddleware
from cms.middleware.toolbar import inster_after_tag, ToolbarMiddleware
from cms.test.testcases import CMSTestCase
from cms.test.util.context_managers import SettingsOverride

class MiddlewareTestCase(CMSTestCase):
    
    def test_01_toolbar_helpers_insert_after_tag(self):
        test_string_1 = None
        test_string_2 = ""
        test_string_3 = "<a href='test'>A test!</a>"
        test_string_4 = "<p>A test!</p>"
        
        tag = 'a'
        
        insertion = '*Insertion*'
        
        result = inster_after_tag(test_string_1, tag, insertion)
        self.assertEqual(result, None)
        result = inster_after_tag(test_string_2, tag, insertion)
        self.assertEqual(result, "")
        result = inster_after_tag(test_string_3, tag, insertion)
        self.assertEqual(result, "<a href='test'>*Insertion*A test!</a>")
        result = inster_after_tag(test_string_4, tag, insertion)
        self.assertEqual(result, "<p>A test!</p>")
        
        
    def test_02_toolbar_middleware_show_toolbar(self):
        class Mock:
            pass
        
        middle = ToolbarMiddleware()
        
        request = Mock()
        response = Mock()
        
        # if request.is_ajax(): 
        setattr(request,'is_ajax', lambda : True)
        result = middle.show_toolbar(request, response)
        self.assertEqual(result, False)
        
        #if response.status_code != 200: 
        setattr(request,'is_ajax', lambda : False)
        setattr(response, 'status_code', 201)
        result = middle.show_toolbar(request, response)
        self.assertEqual(result, False)
        setattr(response, 'status_code', 200)
        
        #if not response['Content-Type'].split(';')[0] in HTML_TYPES:
        setattr(response, '__getitem__', lambda _: 'Whatever')
        result = middle.show_toolbar(request, response)
        self.assertEqual(result, False)
        setattr(response, '__getitem__', lambda _: 'text/html')
        
        #if is_media_request(request):
        setattr(request, 'path', '/media/')
        result = middle.show_toolbar(request, response)
        self.assertEqual(result, False)
        
        setattr(request, 'path', '')
        
        #if "edit" in request.GET: 
        setattr(request, 'GET', ["edit"])
        result = middle.show_toolbar(request, response)
        self.assertEqual(result, True)
        setattr(request, 'GET', [])
        
        #if not hasattr(request, "user"):
        result = middle.show_toolbar(request, response)
        self.assertEqual(result, False)
        setattr(request, 'user', 'test-user')
        
    def test_03_multilingual_middleware_get_lang_from_request(self):
        class Mock:
            pass
        
        middle = MultilingualURLMiddleware()
        
        
        with SettingsOverride(CMS_LANGUAGES = {'klingon':'Klingon'}):
            request = Mock()
            setattr(request, 'session', {})
            setattr(request,'path_info', '/en/whatever')
            setattr(request,'path', '/en/whatever')
            result = middle.get_language_from_request(request)
            self.assertEqual(result, 'en')
        
            setattr(request,'path_info', 'whatever')
            setattr(request,'path', 'whatever')
            setattr(request,'session', {'django_language':'klingon'})
            setattr(request,'COOKIES', {})
            setattr(request,'META', {})
            result = middle.get_language_from_request(request)
            self.assertEqual(result, 'klingon') # the session's language. Nerd.
            
            request = Mock()
            setattr(request,'path_info', 'whatever')
            setattr(request,'path', 'whatever')
            setattr(request,'COOKIES', {'django_language':'klingon'})
            setattr(request,'META', {})
            result = middle.get_language_from_request(request)
            self.assertEqual(result, 'klingon') # the cookies language.
            
            # Now the following should revert to the default language (en)
            setattr(request,'COOKIES', {'django_language':'elvish'})
            result = middle.get_language_from_request(request)
            self.assertEqual(result, 'en') # The default
