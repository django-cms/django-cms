#-*- coding: utf-8 -*-
from __future__ import with_statement
from cms.middleware.multilingual import MultilingualURLMiddleware
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.mock import AttributeObject

class MiddlewareTestCase(CMSTestCase):
    def test_multilingual_middleware_get_lang_from_request(self):
        
        middle = MultilingualURLMiddleware()
        
        KLINGON = 'x-klingon'
        ELVISH = 'x-elvish'
        
        with SettingsOverride(CMS_LANGUAGES={KLINGON: 'Klingon'}):
            request = AttributeObject(
                session={},
                path_info='/en/whatever',
                path='/en/whatever'
            )
            result = middle.get_language_from_request(request)
            self.assertEqual(result, 'en')
            
            
            request = AttributeObject(
                session={
                    'django_language': KLINGON,
                },
                path_info='whatever',
                path='whatever',
                COOKIES={},
                META={},
            )
            result = middle.get_language_from_request(request)
            self.assertEqual(result, KLINGON) # the session's language. Nerd.
            
            
            request = AttributeObject(
                path_info='whatever',
                path='whatever',
                COOKIES={
                    'django_language': KLINGON,
                },
                META={},
            )
            result = middle.get_language_from_request(request)
            self.assertEqual(result, KLINGON) # the cookies language.
            
            # Now the following should revert to the default language (en)
            request.COOKIES['django_language'] = ELVISH
            result = middle.get_language_from_request(request)
            self.assertEqual(result, 'en') # The default
