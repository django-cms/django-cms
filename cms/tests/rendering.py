# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Template, RequestContext
from django.contrib.auth.models import User
from cms.tests.base import CMSTestCase
from cms.models import Page, Title, CMSPlugin, Placeholder
from django.contrib.sites.models import Site
from cms.plugins.text.models import Text
from django.http import HttpRequest
from django.db import connection
from cms.plugin_rendering import render_plugins, PluginContext
from cms import plugin_rendering
from django.forms.widgets import Media

TEMPLATE_NAME = 'tests/rendering/base.html'

def test_plugin_processor(instance, placeholder, rendered_content, original_context):
    return rendered_content + '|test_plugin_processor_ok|'+instance.body+'|'+placeholder.slot+'|'+original_context['original_context_var']

def test_plugin_context_processor(instance, placeholder):
    return {'test_plugin_context_processor': 'test_plugin_context_processor_ok|'+instance.body+'|'+placeholder.slot}

class RenderingTestCase(CMSTestCase):

    def setUp(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        self.login_user(u)

        self.test_data = {
            'title': u'RenderingTestCase-title',
            'slug': u'renderingtestcase-slug',
            'reverse_id': u'renderingtestcase-reverse-id',
            'text_main': u'RenderingTestCase-main',
            'text_sub': u'RenderingTestCase-sub',
        }
        self.test_data2 = {
            'title': u'RenderingTestCase-title2',
            'slug': u'RenderingTestCase-slug2',
            'reverse_id': u'renderingtestcase-reverse-id2',
        }
        self.test_data3 = {
            'title': u'RenderingTestCase-title3',
            'slug': u'RenderingTestCase-slug3',
            'reverse_id': u'renderingtestcase-reverse-id3',
            'text_sub': u'RenderingTestCase-sub3',
        }
        self.insert_test_content()

    def insert_test_content(self):
        # Insert a page
        p = Page(site=Site.objects.get_current(), reverse_id=self.test_data['reverse_id'], template=TEMPLATE_NAME, published=True, publisher_state=1, publisher_is_draft=False)
        p.save()
        t = Title(page=p, language=settings.LANGUAGES[0][0], slug=self.test_data['slug'], title=self.test_data['title'])
        t.save()
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders = {}
        for placeholder in p.placeholders.all():
            self.test_placeholders[placeholder.slot] = placeholder
        # Insert another page that is not the home page
        p2 = Page(parent=p, site=Site.objects.get_current(), reverse_id=self.test_data2['reverse_id'], template=TEMPLATE_NAME, published=True, publisher_state=1, publisher_is_draft=False)
        p2.save()
        t2 = Title(page=p2, language=settings.LANGUAGES[0][0], slug=self.test_data2['slug'], title=self.test_data2['title'])
        t2.save()
        # Insert some test Text plugins
        pl = Text(plugin_type='TextPlugin', page=p, language=settings.LANGUAGES[0][0], placeholder=self.test_placeholders['main'], position=0, body=self.test_data['text_main'])
        pl.insert_at(None, commit=True)
        pl = Text(plugin_type='TextPlugin', page=p, language=settings.LANGUAGES[0][0], placeholder=self.test_placeholders['sub'], position=0, body=self.test_data['text_sub'])
        pl.insert_at(None, commit=True)

        # Insert another page that is not the home page
        p3 = Page(parent=p2, site=Site.objects.get_current(), reverse_id=self.test_data3['reverse_id'], template=TEMPLATE_NAME, published=True, publisher_state=1, publisher_is_draft=False)
        p3.save()
        t3 = Title(page=p3, language=settings.LANGUAGES[0][0], slug=self.test_data3['slug'], title=self.test_data3['title'])
        t3.save()
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders3 = {}
        for placeholder in p3.placeholders.all():
            self.test_placeholders3[placeholder.slot] = placeholder
        # # Insert some test Text plugins
        pl = Text(plugin_type='TextPlugin', page=p3, language=settings.LANGUAGES[0][0], placeholder=self.test_placeholders3['sub'], position=0, body=self.test_data3['text_sub'])
        pl.insert_at(None, commit=True)

        # Reload test pages
        self.test_page = Page.objects.get(pk=p.pk)
        self.test_page2 = Page.objects.get(pk=p2.pk)
        self.test_page3 = Page.objects.get(pk=p3.pk)

    def get_context(self, context_vars={}):
        request = self.get_request()
        return RequestContext(request, context_vars)

    def get_request(self, *args, **kwargs):
        request = super(RenderingTestCase, self).get_request(*args, **kwargs)
        request.current_page = self.test_page
        request.placeholder_media = Media()
        return request

    def init_render_settings(self):
        settings.CMS_PLUGIN_PROCESSORS = ()
        settings.CMS_PLUGIN_CONTEXT_PROCESSORS = ()
        settings.CMS_TEMPLATES = (TEMPLATE_NAME, ''),

    def strip_rendered(self, content):
        return content.strip().replace(u"\n", u"")

    def render(self, template, context_vars={}):
        self.init_render_settings()
        c = self.get_context(context_vars)
        t = Template(template)
        r = t.render(c)
        return self.strip_rendered(r)

    def test_00_details_view(self):
        """
        Tests that the `detail` view is working.
        """
        self.init_render_settings()
        from cms.views import details
        response = details(self.get_request(), page_id=self.test_page.pk)
        r = self.strip_rendered(response.content)
        self.assertEqual(r, u'|'+self.test_data['text_main']+u'|'+self.test_data['text_sub']+u'|')
        
    def test_01_processors(self):
        """
        Tests that default plugin context processors are working, that plugin processors and plugin context processors
        can be defined in settings and are working and that extra plugin context processors can be passed to PluginContext.
        """
        settings.CMS_PLUGIN_PROCESSORS = ('cms.tests.rendering.test_plugin_processor',)
        settings.CMS_PLUGIN_CONTEXT_PROCESSORS = ('cms.tests.rendering.test_plugin_context_processor',)
        def test_passed_plugin_context_processor(instance, placeholder):
            return {'test_passed_plugin_context_processor': 'test_passed_plugin_context_processor_ok'}
        t = u'{% load cms_tags %}'+ \
            u'{{ plugin.counter }}|{{ plugin.instance.body }}|{{ test_passed_plugin_context_processor }}|{{ test_plugin_context_processor }}'
        instance, plugin = CMSPlugin.objects.all()[0].get_plugin_instance()
        instance.render_template = Template(t)
        context = PluginContext({'original_context_var': 'original_context_var_ok'}, instance, self.test_placeholders['main'], processors=(test_passed_plugin_context_processor,))
        plugin_rendering._standard_processors = {}
        c = render_plugins((instance,), context, self.test_placeholders['main'])
        r = "".join(c) 
        self.assertEqual(r, u'1|'+self.test_data['text_main']+'|test_passed_plugin_context_processor_ok|test_plugin_context_processor_ok|'+self.test_data['text_main']+'|main|test_plugin_processor_ok|'+self.test_data['text_main']+'|main|original_context_var_ok')
        plugin_rendering._standard_processors = {}

    def test_02_placeholder(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% placeholder "main" %}|{% placeholder "empty" %}'
        r = self.render(t)
        self.assertEqual(r, u'|'+self.test_data['text_main']+'|')

    def test_03_placeholderor(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% placeholder "empty" or %}No content{% endplaceholder %}'
        r = self.render(t)
        self.assertEqual(r, u'|No content')

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
        settings.DEBUG = False
        t = u'{% load cms_tags %}'+ \
            u'|{% page_url -1 %}'
        r = self.render(t)
        from django.core import mail
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals("'pk': -1" in mail.outbox[0].body, True)
        """
        # mail_managers is no longer used
        self.assertTrue(True)

    def test_09_inherit_placeholder(self):
        t = u'{% load cms_tags %}'+ \
            u'|{% placeholder "main" inherit %}|{% placeholder "sub" %}'
        self.old_test_page = self.test_page
        self.test_page = self.test_page3
        r = self.render(t)
        self.test_page = self.old_test_page
        self.assertEqual(r, u'|'+self.test_data['text_main']+'|'+self.test_data3['text_sub'])

