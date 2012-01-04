#-*- coding: utf-8 -*-
from __future__ import with_statement
from cms.middleware.multilingual import MultilingualURLMiddleware, HAS_LANG_PREFIX_RE
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.mock import AttributeObject
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import django

class MiddlewareTestCase(CMSTestCase):
    def test_multilingual_middleware_get_lang_from_request(self):
        
        middle = MultilingualURLMiddleware()
        
        KLINGON = 'x-klingon'
        ELVISH = 'x-elvish'
        
        with SettingsOverride(CMS_LANGUAGES=((KLINGON, 'Klingon'),)):
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


    def test_multilingual_middleware_ignores_static_url(self):

        middle = MultilingualURLMiddleware()
        KLINGON = 'x-klingon'
        
        with SettingsOverride(CMS_LANGUAGES=((KLINGON, 'Klingon'),)):
            request = AttributeObject(
                session={},
                path_info='whatever',
                path='whatever',
                COOKIES={
                    'django_language': KLINGON,
                },
                META = {},
                LANGUAGE_CODE = KLINGON
            )
            html = """<ul>
                <li><a href="/some-page/">some page</a></li>
                <li><a href="%simages/some-media-file.jpg">some media file</a></li>
                <li><a href="%simages/some-static-file.jpg">some static file</a></li>
                <li><a href="%simages/some-admin-file.jpg">some admin media file</a></li>
                <li><a href="%simages/some-other-file.jpg">some static file</a></li>
                </ul>""" %(
                    settings.MEDIA_URL,
                    settings.STATIC_URL,
                    settings.ADMIN_MEDIA_PREFIX,
                    '/some-path/',
                )
            
            response = middle.process_response(request,HttpResponse(html))
            
            # These paths shall be prefixed
            self.assertTrue('href="/%s/some-page/' %KLINGON in response.content)
            self.assertTrue('href="/%s%simages/some-other-file.jpg' %(KLINGON, '/some-path/') in response.content)

            # These shall not
            self.assertTrue('href="%simages/some-media-file.jpg' %settings.MEDIA_URL in response.content)
            self.assertTrue('href="%simages/some-static-file.jpg' %settings.STATIC_URL in response.content)            
            self.assertTrue('href="%simages/some-admin-file.jpg' %settings.ADMIN_MEDIA_PREFIX in response.content)
            
    
    def test_multilingual_middleware_handles_redirections(self):

        middle = MultilingualURLMiddleware()

        request = AttributeObject(
            session={},
            path_info='whatever',
            path='whatever',
            COOKIES={
                'django_language': 'en',
            },
            META = {},
            LANGUAGE_CODE = 'en'
        )
        
        # Don't re-prefix
        response = middle.process_response(request,HttpResponseRedirect('/en/some-path/'))
        self.assertTrue(response['Location'] == '/en/some-path/')

        response = middle.process_response(request,HttpResponseRedirect('%ssome-path/'%settings.MEDIA_URL))
        self.assertTrue(response['Location'] == '%ssome-path/' %settings.MEDIA_URL)

        response = middle.process_response(request,HttpResponseRedirect('%ssome-path/'%settings.STATIC_URL))
        self.assertTrue(response['Location'] == '%ssome-path/' %settings.STATIC_URL)
        

        # Prefix
        response = middle.process_response(request,HttpResponseRedirect('/xx/some-path/'))
        self.assertTrue(response['Location'] == '/en/xx/some-path/')

