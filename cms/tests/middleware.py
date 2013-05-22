#-*- coding: utf-8 -*-
from __future__ import with_statement
from cms.middleware.multilingual import MultilingualURLMiddleware, HAS_LANG_PREFIX_RE
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.mock import AttributeObject
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import django
from cms.templatetags.cms_admin import admin_static_url

class MiddlewareTestCase(CMSTestCase):
    def test_multilingual_middleware_get_lang_from_request(self):
        
        middle = MultilingualURLMiddleware()
        
        FRENCH = 'fr'
        ELVISH = 'x-elvish'
        
        with SettingsOverride(CMS_LANGUAGES=((FRENCH, 'French'),("it", "Italian")), CMS_FRONTEND_LANGUAGES=(FRENCH,)):
            request = AttributeObject(
                session={},
                path_info='/it/whatever',
                path='/it/whatever',
                COOKIES={},
                META={},
            )
            result = middle.get_language_from_request(request)
            self.assertEqual(result, 'en')#falls back to default
            
            
            request = AttributeObject(
                session={
                    'django_language': FRENCH,
                },
                path_info='whatever',
                path='whatever',
                COOKIES={},
                META={},
            )
            result = middle.get_language_from_request(request)
            self.assertEqual(result, FRENCH) # the session's language.
            
            
            cookie_dict = {}
            cookie_dict[settings.LANGUAGE_COOKIE_NAME] = FRENCH
            
            request = AttributeObject(
                path_info='whatever',
                path='whatever',
                COOKIES=cookie_dict,
                META={},
            )
            result = middle.get_language_from_request(request)
            self.assertEqual(result, FRENCH) # the cookies language.
            
            # Now the following should revert to the default language (en)
            request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = ELVISH
            result = middle.get_language_from_request(request)
            self.assertEqual(result, 'en') # The default


    def test_multilingual_middleware_ignores_static_url(self):

        middle = MultilingualURLMiddleware()
        FRENCH = 'x-FRENCH'
        
        with SettingsOverride(CMS_LANGUAGES=((FRENCH, 'FRENCH'),)):

            cookie_dict = {}
            cookie_dict[settings.LANGUAGE_COOKIE_NAME] = FRENCH

            request = AttributeObject(
                session={},
                path_info='whatever',
                path='whatever',
                COOKIES=cookie_dict,
                META = {},
                LANGUAGE_CODE = FRENCH
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
                    admin_static_url(),
                    '/some-path/',
                )
            
            response = middle.process_response(request,HttpResponse(html))
            
            # These paths shall be prefixed
            self.assertTrue('href="/%s/some-page/' %FRENCH in response.content)
            self.assertTrue('href="/%s%simages/some-other-file.jpg' %(FRENCH, '/some-path/') in response.content)

            # These shall not
            self.assertTrue('href="%simages/some-media-file.jpg' %settings.MEDIA_URL in response.content)
            self.assertTrue('href="%simages/some-static-file.jpg' %settings.STATIC_URL in response.content)            
            self.assertTrue('href="%simages/some-admin-file.jpg' %admin_static_url() in response.content)
            
    
    def test_multilingual_middleware_handles_redirections(self):

        middle = MultilingualURLMiddleware()

        cookie_dict = {}
        cookie_dict[settings.LANGUAGE_COOKIE_NAME] = 'en'

        request = AttributeObject(
            session={},
            path_info='whatever',
            path='whatever',
            COOKIES=cookie_dict,
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

    def test_multilingual_middleware_custom_language_cookie_name(self):
        middle = MultilingualURLMiddleware()

        FRENCH = 'fr'
        CUSTOM_COOKIE_NAME = 'test_lang_cookie'
        
        with SettingsOverride(
                              CMS_LANGUAGES=((FRENCH, 'French'),("it", "Italian")), 
                              CMS_FRONTEND_LANGUAGES=(FRENCH,),
                              LANGUAGE_COOKIE_NAME=CUSTOM_COOKIE_NAME):

            request = AttributeObject(
                path_info='whatever',
                path='whatever',
                COOKIES={},
                META={},
            )

            def _get_cookie_value(response, key):
                """
                Returns the value of a cookie from the response
                """
                return response.cookies[key].value

            # check that the name for the language cookie is set correctly
            # honoring the LANGUAGE_COOKIE_NAME
            response = middle.process_response(request,
                                            HttpResponseRedirect(request.path))
            self.assertTrue(CUSTOM_COOKIE_NAME in response.cookies.keys())
            self.assertFalse('django_language' in response.cookies.keys())
            self.assertEqual(_get_cookie_value(response, CUSTOM_COOKIE_NAME),
                             'en')

            # check that the language is correctly read from the cookie
            request.COOKIES[CUSTOM_COOKIE_NAME] = FRENCH

            result = middle.get_language_from_request(request)
            self.assertEqual(result, FRENCH)
