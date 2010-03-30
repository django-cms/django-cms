# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Template, RequestContext
from django.contrib.auth.models import User
from cms.tests.base import CMSTestCase
from cms.models import Page, Title, CMSPlugin
from django.contrib.sites.models import Site
from cms.plugins.text.models import Text
from django.http import HttpRequest
from django.db import connection
from cms.plugin_rendering import render_plugins, PluginContext
from cms import plugin_rendering

import logging

def test_plugin_processor(instance, placeholder, rendered_content, original_context):
    return rendered_content + '|test_plugin_processor_ok'

def test_plugin_context_processor(instance, placeholder):
    return {'test_plugin_context_processor': 'test_plugin_context_processor_ok'}

class RenderingTestCase(CMSTestCase):

    def setUp(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        self.login_user(u)

        self.test_data = {
            'title': u'Templatetags Test',
            'slug': u'templatetags-test-slug',
            'reverse_id': u'templatetags-test-reverse-id',
            'text_main': u'Templatetags Test Main',
            'text_sub': u'Templatetags Test Sub',
        }
        self.test_data2 = {
            'title': u'Templatetags Test 2',
            'slug': u'templatetags-test-slug2',
            'reverse_id': u'templatetags-test-reverse-id2',
        }
        self.insert_test_content()

    def insert_test_content(self):
        # Insert a page
        p = Page(site=Site.objects.get_current(), reverse_id=self.test_data['reverse_id'], published=True, publisher_state=1, publisher_is_draft=False)
        p.save()
        t = Title(page=p, language=settings.LANGUAGES[0][0], slug=self.test_data['slug'], title=self.test_data['title'])
        t.save()
        # Insert another page that is not the home page
        p2 = Page(site=Site.objects.get_current(), reverse_id=self.test_data2['reverse_id'], published=True, publisher_state=1, publisher_is_draft=False)
        p2.save()
        t2 = Title(page=p2, language=settings.LANGUAGES[0][0], slug=self.test_data2['slug'], title=self.test_data2['title'])
        t2.save()
        # Insert some test Text plugins
        pl = Text(plugin_type='TextPlugin', page=p, language=settings.LANGUAGES[0][0], placeholder='main', position=0, body=self.test_data['text_main'], publisher_state=1, publisher_is_draft=False)
        pl.insert_at(None, commit=True)
        pl = Text(plugin_type='TextPlugin', page=p, language=settings.LANGUAGES[0][0], placeholder='sub', position=0, body=self.test_data['text_sub'], publisher_state=1, publisher_is_draft=False)
        pl.insert_at(None, commit=True)
        # Reload test pages
        self.test_page = Page.objects.get(pk=p.pk)
        self.test_page2 = Page.objects.get(pk=p2.pk)

    def get_context(self, context_vars={}):
        request = self.get_request()
        request.current_page = self.test_page
        return RequestContext(request, context_vars)

    def render(self, template, context_vars={}):
        settings.CMS_PLUGIN_PROCESSORS = ()
        settings.CMS_PLUGIN_CONTEXT_PROCESSORS = ()
        c = self.get_context(context_vars)
        t = Template(template)
        r = t.render(c)
        r = r.strip().replace(u"\n", u"")
        return r

    def test_01_processors(self):
        """
        Tests that default plugin context processors are working, that plugin processors and plugin context processors
        can be defined in settings and are working and that extra plugin context processors can be passed to PluginContext.
        """
        settings.CMS_PLUGIN_PROCESSORS = ('cms.tests.templatetags.test_plugin_processor',)
        settings.CMS_PLUGIN_CONTEXT_PROCESSORS = ('cms.tests.templatetags.test_plugin_context_processor',)
        def test_passed_plugin_context_processor(instance, placeholder):
            return {'test_passed_plugin_context_processor': 'test_passed_plugin_context_processor_ok'}
        t = u'{% load cms_tags %}'+ \
            u'{{ plugin.counter }}|{{ plugin.instance.body }}|{{ test_passed_plugin_context_processor }}|{{ test_plugin_context_processor }}'
        instance, plugin = CMSPlugin.objects.all()[0].get_plugin_instance()
        instance.render_template = Template(t)
        context = PluginContext(None, instance, 'main', processors=(test_passed_plugin_context_processor,))
        c = render_plugins((instance,), context, 'main')
        r = "".join(c) 
        self.assertEqual(r, u'1|'+self.test_data['text_main']+'|test_passed_plugin_context_processor_ok|test_plugin_context_processor_ok|test_plugin_processor_ok')
        plugin_rendering._standard_processors = {}

    def test_02_placeholder(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% placeholder "main" %}|{% placeholder "none" %}'
        r = self.render(t)
        self.assertEqual(r, u'|'+self.test_data['text_main']+'|')

    def test_03_placeholderor(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% placeholderor "none" %}Does not exist{% endplaceholderor %}'
        r = self.render(t)
        self.assertEqual(r, u'|Does not exist')

    def test_04_show_placeholder(self):
        """
        Tests the {% show_placeholder %} templatetag, using lookup by pk/dict/reverse_id and passing a Page object.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% show_placeholder "main" '+str(self.test_page.pk)+' %}'+ \
            u'|{% show_placeholder "main" test_dict %}'+ \
            u'|{% show_placeholder "sub" "'+str(self.test_page.reverse_id)+'" %}'+ \
            u'|{% show_placeholder "sub" test_page %}'
        r = self.render(t, {'test_page': self.test_page, 'test_dict': {'pk': self.test_page.pk}})
        self.assertEqual(r, (u'|'+self.test_data['text_main'])*2+(u'|'+self.test_data['text_sub'])*2)

    def test_05_show_uncached_placeholder(self):
        """
        Tests the {% show_uncached_placeholder %} templatetag, using lookup by pk/dict/reverse_id and passing a Page object.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% show_uncached_placeholder "main" '+str(self.test_page.pk)+' %}'+ \
            u'|{% show_uncached_placeholder "main" test_dict %}'+ \
            u'|{% show_uncached_placeholder "sub" "'+str(self.test_page.reverse_id)+'" %}'+ \
            u'|{% show_uncached_placeholder "sub" test_page %}'
        r = self.render(t, {'test_page': self.test_page, 'test_dict': {'pk': self.test_page.pk}})
        self.assertEqual(r, (u'|'+self.test_data['text_main'])*2+(u'|'+self.test_data['text_sub'])*2)

    def test_06_page_url(self):
        """
        Tests the {% page_url %} templatetag, using lookup by pk/dict/reverse_id and passing a Page object.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% page_url '+str(self.test_page2.pk)+' %}'+ \
            u'|{% page_url test_dict %}'+ \
            u'|{% page_url "'+str(self.test_page2.reverse_id)+'" %}'+ \
            u'|{% page_url test_page %}'
        r = self.render(t, {'test_page': self.test_page2, 'test_dict': {'pk': self.test_page2.pk}})
        self.assertEqual(r, (u'|'+self.test_page2.get_absolute_url())*4)

    def test_07_page_attribute(self):
        """
        Tests the {% page_attribute %} templatetag, using current page, lookup by pk/dict/reverse_id and passing a Page object.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% page_attribute title %}'+ \
            u'|{% page_attribute title '+str(self.test_page2.pk)+' %}'+ \
            u'|{% page_attribute title test_dict %}'+ \
            u'|{% page_attribute slug "'+str(self.test_page2.reverse_id)+'" %}'+ \
            u'|{% page_attribute slug test_page %}'
        r = self.render(t, {'test_page': self.test_page2, 'test_dict': {'pk': self.test_page2.pk}})
        self.assertEqual(r, u'|'+self.test_data['title']+(u'|'+self.test_data2['title'])*2+(u'|'+self.test_data2['slug'])*2)

    def test_08_mail_managers(self):
        """
        Tests that mail_managers() is called from the templatetags if a page cannot be found by page_lookup argument.
        """
        settings.DEBUG = False
        t = u'{% load cms_tags %}'+ \
            u'|{% page_url -1 %}'
        r = self.render(t)
        from django.core import mail
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals("'pk': -1" in mail.outbox[0].body, True)
