# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms import plugin_rendering
from cms.api import create_page, add_plugin
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_rendering import (render_plugins, PluginContext, 
    render_placeholder_toolbar)
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride, ChangeModel
from cms.test_utils.util.mock import AttributeObject
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseRedirect
from django.template import Template, RequestContext
from sekizai.context import SekizaiContext

TEMPLATE_NAME = 'tests/rendering/base.html'

def test_plugin_processor(instance, placeholder, rendered_content, original_context):
    original_context_var = original_context['original_context_var']
    return '%s|test_plugin_processor_ok|%s|%s|%s' % (rendered_content,
                                                   instance.body,
                                                   placeholder.slot,
                                                   original_context_var)

def test_plugin_context_processor(instance, placeholder):
    content = 'test_plugin_context_processor_ok|'+instance.body+'|'+placeholder.slot
    return {'test_plugin_context_processor': content}


class RenderingTestCase(SettingsOverrideTestCase):
    
    settings_overrides = {
        'CMS_TEMPLATES': [(TEMPLATE_NAME, TEMPLATE_NAME), ('extra_context.html', 'extra_context.html')],
        'CMS_MODERATOR': False,
    }

    def setUp(self):
        super(RenderingTestCase, self).setUp()
        self.test_user = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        self.test_user.set_password("test")
        self.test_user.save()
        with self.login_user_context(self.test_user):
    
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
            self.test_data4 = {
                'title': u'RenderingTestCase-title3',
                'no_extra': u'no extra var!',
                'placeholderconf': {'extra_context': {'extra_context': {'extra_var': 'found extra var'}}},
                'extra': u'found extra var',
            }
            self.insert_test_content()

    def insert_test_content(self):
        # Insert a page
        p = create_page(self.test_data['title'], TEMPLATE_NAME, 'en',
                    slug=self.test_data['slug'], created_by=self.test_user,
                    reverse_id=self.test_data['reverse_id'], published=True)
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders = {}
        for placeholder in p.placeholders.all():
            self.test_placeholders[placeholder.slot] = placeholder
        # Insert another page that is not the home page
        p2 = create_page(self.test_data2['title'], TEMPLATE_NAME, 'en',
                    parent=p, slug=self.test_data2['slug'], published=True,
                    reverse_id=self.test_data2['reverse_id'])
        # Insert some test Text plugins
        add_plugin(self.test_placeholders['main'], 'TextPlugin', 'en',
                   body=self.test_data['text_main'])
        add_plugin(self.test_placeholders['sub'], 'TextPlugin', 'en',
                   body=self.test_data['text_sub'])

        # Insert another page that is not the home page
        p3 = create_page(self.test_data3['title'], TEMPLATE_NAME, 'en',
                         slug=self.test_data3['slug'], parent=p2,
                         reverse_id=self.test_data3['reverse_id'], published=True)
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders3 = {}
        for placeholder in p3.placeholders.all():
            self.test_placeholders3[placeholder.slot] = placeholder
        # # Insert some test Text plugins
        add_plugin(self.test_placeholders3['sub'], 'TextPlugin', 'en',
                   body=self.test_data3['text_sub'])
                   
        # Insert another page that is not the home
        p4 = create_page(self.test_data4['title'], 'extra_context.html', 'en', parent=p)
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders4 = {}
        for placeholder in p4.placeholders.all():
            self.test_placeholders4[placeholder.slot] = placeholder
        # Insert some test plugins
        add_plugin(self.test_placeholders4['extra_context'], 'ExtraContextPlugin', 'en')        

        # Reload test pages
        self.test_page = self.reload(p)
        self.test_page2 = self.reload(p2)
        self.test_page3 = self.reload(p3)
        self.test_page4 = self.reload(p4)
        
    def get_context(self, page, context_vars={}):
        request = self.get_request(page)
        return RequestContext(request, context_vars)

    def get_request(self, page, *args, **kwargs):
        request = super(RenderingTestCase, self).get_request(*args, **kwargs)
        request.current_page = page
        return request

    def strip_rendered(self, content):
        return content.strip().replace(u"\n", u"")

    def render(self, template, page, context_vars={}):
        with SettingsOverride(CMS_TEMPLATES=[(TEMPLATE_NAME, '')]):
            c = self.get_context(page, context_vars)
            t = Template(template)
            r = t.render(c)
            return self.strip_rendered(r)

    def test_details_view(self):
        """
        Tests that the `detail` view is working.
        """
        with SettingsOverride(CMS_TEMPLATES=[(TEMPLATE_NAME, '')]):
            from cms.views import details
            response = details(self.get_request(self.test_page), '')
            r = self.strip_rendered(response.content)
            self.assertEqual(r, u'|'+self.test_data['text_main']+u'|'+self.test_data['text_sub']+u'|')
        
    def test_processors(self):
        """
        Tests that default plugin context processors are working, that plugin processors and plugin context processors
        can be defined in settings and are working and that extra plugin context processors can be passed to PluginContext.
        """
        with SettingsOverride(
                CMS_PLUGIN_PROCESSORS = ('cms.tests.rendering.test_plugin_processor',),
                CMS_PLUGIN_CONTEXT_PROCESSORS = ('cms.tests.rendering.test_plugin_context_processor',),
            ):
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
    
    def test_placeholder(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% placeholder "main" %}|{% placeholder "empty" %}'
        r = self.render(t, self.test_page)
        self.assertEqual(r, u'|'+self.test_data['text_main']+'|')
        

    def test_placeholder_extra_context(self):
        t = u'{% load cms_tags %}{% placeholder "extra_context" %}'
        r = self.render(t, self.test_page4)
        self.assertEqual(r, self.test_data4['no_extra'])
        with SettingsOverride(CMS_PLACEHOLDER_CONF=self.test_data4['placeholderconf']):
            r = self.render(t, self.test_page4)
        self.assertEqual(r, self.test_data4['extra'])

    def test_placeholderor(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% placeholder "empty" or %}No content{% endplaceholder %}'
        r = self.render(t, self.test_page)
        self.assertEqual(r, u'|No content')

    def test_show_placeholder(self):
        """
        Tests the {% show_placeholder %} templatetag, using lookup by pk/dict/reverse_id and passing a Page object.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% show_placeholder "main" '+str(self.test_page.pk)+' %}'+ \
            u'|{% show_placeholder "main" test_dict %}'+ \
            u'|{% show_placeholder "sub" "'+str(self.test_page.reverse_id)+'" %}'+ \
            u'|{% show_placeholder "sub" test_page %}'
        r = self.render(t, self.test_page, {'test_page': self.test_page, 'test_dict': {'pk': self.test_page.pk}})
        self.assertEqual(r, (u'|'+self.test_data['text_main'])*2+(u'|'+self.test_data['text_sub'])*2)
        
    def test_show_placeholder_extra_context(self):
        t = u'{% load cms_tags %}{% show_placeholder "extra_context" '+str(self.test_page4.pk)+' %}'
        r = self.render(t, self.test_page4)
        self.assertEqual(r, self.test_data4['no_extra'])
        with SettingsOverride(CMS_PLACEHOLDER_CONF=self.test_data4['placeholderconf']):
            r = self.render(t, self.test_page4)
        self.assertEqual(r, self.test_data4['extra'])
            
    def test_show_uncached_placeholder_by_pk(self):
        """
        Tests the {% show_uncached_placeholder %} templatetag, using lookup by pk.
        """
        template = u'{%% load cms_tags %%}{%% show_uncached_placeholder "main" %s %%}' % self.test_page.pk
        output = self.render(template, self.test_page)
        self.assertEqual(output, self.test_data['text_main'])

    def test_show_uncached_placeholder_by_lookup_dict(self):
        template = u'{% load cms_tags %}{% show_uncached_placeholder "main" test_dict %}'
        output = self.render(template, self.test_page, {'test_dict': {'pk': self.test_page.pk}})
        self.assertEqual(output, self.test_data['text_main'])

    def test_show_uncached_placeholder_by_reverse_id(self):
        template = u'{%% load cms_tags %%}{%% show_uncached_placeholder "sub" "%s" %%}' % self.test_page.reverse_id
        output = self.render(template, self.test_page)
        self.assertEqual(output, self.test_data['text_sub'])

    def test_show_uncached_placeholder_by_page(self):
        template = u'{% load cms_tags %}{% show_uncached_placeholder "sub" test_page %}'
        output = self.render(template, self.test_page, {'test_page': self.test_page})
        self.assertEqual(output, self.test_data['text_sub'])
        
    def test_page_url_by_pk(self):
        template = u'{%% load cms_tags %%}{%% page_url %s %%}' % self.test_page2.pk
        output = self.render(template, self.test_page)
        self.assertEqual(output, self.test_page2.get_absolute_url())
        
    def test_page_url_by_dictionary(self):
        template = u'{% load cms_tags %}{% page_url test_dict %}'
        output =  self.render(template, self.test_page, {'test_dict': {'pk': self.test_page2.pk}})
        self.assertEqual(output, self.test_page2.get_absolute_url())
        
    def test_page_url_by_reverse_id(self):
        template = u'{%% load cms_tags %%}{%% page_url "%s" %%}' % self.test_page2.reverse_id
        output = self.render(template, self.test_page)
        self.assertEqual(output, self.test_page2.get_absolute_url())
        
    def test_page_url_by_reverse_id_not_on_a_page(self):
        template = u'{%% load cms_tags %%}{%% page_url "%s" %%}' % self.test_page2.reverse_id
        output = self.render(template, None)
        self.assertEqual(output, self.test_page2.get_absolute_url())
    
    def test_page_url_by_page(self):
        template = u'{% load cms_tags %}{% page_url test_page %}'
        output = self.render(template, self.test_page, {'test_page': self.test_page2})
        self.assertEqual(output, self.test_page2.get_absolute_url())

    def test_page_attribute(self):
        """
        Tests the {% page_attribute %} templatetag, using current page, lookup by pk/dict/reverse_id and passing a Page object.
        """
        t = u'{% load cms_tags %}'+ \
            u'|{% page_attribute title %}'+ \
            u'{% page_attribute title as title %}'+ \
            u'|{{ title }}'+ \
            u'|{% page_attribute title '+str(self.test_page2.pk)+' %}'+ \
            u'{% page_attribute title '+str(self.test_page2.pk)+' as title %}'+ \
            u'|{{ title }}'+ \
            u'|{% page_attribute title test_dict %}'+ \
            u'{% page_attribute title test_dict as title %}'+ \
            u'|{{ title }}'+ \
            u'|{% page_attribute slug "'+str(self.test_page2.reverse_id)+'" %}'+ \
            u'{% page_attribute slug "'+str(self.test_page2.reverse_id)+'" as slug %}'+ \
            u'|{{ slug }}'+ \
            u'|{% page_attribute slug test_page %}'+ \
            u'{% page_attribute slug test_page as slug %}'+ \
            u'|{{ slug }}'
        r = self.render(t, self.test_page, {'test_page': self.test_page2, 'test_dict': {'pk': self.test_page2.pk}})
        self.assertEqual(r, (u'|'+self.test_data['title'])*2+(u'|'+self.test_data2['title'])*4+(u'|'+self.test_data2['slug'])*4)

    def test_inherit_placeholder(self):
        t = u'{% load cms_tags %}'+ \
            u'|{% placeholder "main" inherit %}|{% placeholder "sub" %}'
        r = self.render(t, self.test_page3)
        self.assertEqual(r, u'|'+self.test_data['text_main']+'|'+self.test_data3['text_sub'])
        
    def test_detail_view_404_when_no_language_is_found(self):
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=[],
                              CMS_LANGUAGES=[
                                  ('x-klingon', 'Klingon'),
                                  ('x-elvish', 'Elvish')
                              ]):
            from cms.views import details
            request = AttributeObject(
                REQUEST={'language': 'x-elvish'},
                GET=[],
                session={},
                path='/',
                user=self.test_user,
                current_page=None,
                method='GET',
            )
            self.assertRaises(Http404, details, request, '')

    def test_detail_view_fallback_language(self):
        '''
        Ask for a page in elvish (doesn't exist), and assert that it fallsback
        to English
        '''
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=[],
                              CMS_LANGUAGE_CONF={
                                  'x-elvish': ['x-klingon', 'en',]
                              },
                              CMS_LANGUAGES=[
                                  ('x-klingon', 'Klingon'),
                                  ('x-elvish', 'Elvish'),
                              ]):
            from cms.views import details
            request = AttributeObject(
                REQUEST={'language': 'x-elvish'},
                GET=[],
                session={},
                path='/',
                user=self.test_user,
                current_page=None,
                method='GET',
            )

            response = details(request, '')
            self.assertTrue(isinstance(response,HttpResponseRedirect))
            
    def test_extra_context_isolation(self):
        with ChangeModel(self.test_page, template='extra_context.html'):
            response = self.client.get(self.test_page.get_absolute_url())
            self.assertTrue('width' not in response.context)

    def test_render_placeholder_toolbar(self):
        placeholder = Placeholder()
        placeholder.slot = 'test'
        placeholder.pk = placeholder.id = 99
        context = SekizaiContext()
        context['request'] = AttributeObject(
            REQUEST={'language': 'en'},
            GET=[],
            session={},
            path='/',
            user=self.test_user,
            current_page=None,
            method='GET',
        )
        classes = [
            "cms_placeholder-bar-%s" % placeholder.pk,
            "cms_placeholder_slot::test",
        ]
        output = render_placeholder_toolbar(placeholder, context, '', 'test')
        for cls in classes:
            self.assertTrue(cls in output, '%r is not in %r' % (cls, output))

    def test_placeholder_name_toolbar(self):
        placeholder_conf_name = 'test_placeholder'
        placeholder_conf_tag = '<div class="cms_placeholder-title">%s</div>' % placeholder_conf_name
        with SettingsOverride(CMS_PLACEHOLDER_CONF = {
                                  'test': {'name':placeholder_conf_name}
                              }):
            placeholder = Placeholder()
            placeholder.slot = 'test'
            placeholder.pk = placeholder.id = 99
            context = SekizaiContext()
            context['request'] = AttributeObject(
                REQUEST={'language': 'en'},
                GET=[],
                session={},
                path='/',
                user=self.test_user,
                current_page=None,
                method='GET',
                )
            classes = [
                "cms_placeholder-bar-%s" % placeholder.pk,
                "cms_placeholder_slot::test",
                ]
            output = render_placeholder_toolbar(placeholder, context, '', 'test')
            self.assertTrue(placeholder_conf_tag in output, 'placeholder name %r is not in %r' % (placeholder_conf_name, output))
