# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.template import Template
from django.test.utils import override_settings
from sekizai.context import SekizaiContext

from cms import plugin_rendering
from cms.api import create_page, add_plugin
from cms.cache.placeholder import get_placeholder_cache
from cms.models import Page, Placeholder, CMSPlugin
from cms.plugin_rendering import render_plugins, PluginContext, render_placeholder_toolbar
from cms.test_utils.project.placeholderapp.models import Example1
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import ChangeModel
from cms.test_utils.util.mock import AttributeObject
from cms.toolbar.toolbar import CMSToolbar
from cms.views import details

TEMPLATE_NAME = 'tests/rendering/base.html'


def sample_plugin_processor(instance, placeholder, rendered_content, original_context):
    original_context_var = original_context['original_context_var']
    return '%s|test_plugin_processor_ok|%s|%s|%s' % (
        rendered_content,
        instance.body,
        placeholder.slot,
        original_context_var
    )


def sample_plugin_context_processor(instance, placeholder, original_context):
    content = 'test_plugin_context_processor_ok|' + instance.body + '|' + \
        placeholder.slot + '|' + original_context['original_context_var']
    return {
        'test_plugin_context_processor': content,
    }


@override_settings(
    CMS_TEMPLATES=[(TEMPLATE_NAME, TEMPLATE_NAME), ('extra_context.html', 'extra_context.html')],
)
class RenderingTestCase(CMSTestCase):

    def setUp(self):
        super(RenderingTestCase, self).setUp()
        self.test_user = self._create_user("test", True, True)

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
            self.test_data5 = {
                'title': u'RenderingTestCase-title5',
                'slug': u'RenderingTestCase-slug5',
                'reverse_id': u'renderingtestcase-reverse-id5',
                'text_main': u'RenderingTestCase-main-page5',
                'text_sub': u'RenderingTestCase-sub5',
            }
            self.test_data6 = {
                'title': u'RenderingTestCase-title6',
                'slug': u'RenderingTestCase-slug6',
                'reverse_id': u'renderingtestcase-reverse-id6',
                'text_sub': u'RenderingTestCase-sub6',
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
            # Insert some test Text plugins
        add_plugin(self.test_placeholders['main'], 'TextPlugin', 'en',
                   body=self.test_data['text_main'])
        add_plugin(self.test_placeholders['sub'], 'TextPlugin', 'en',
                   body=self.test_data['text_sub'])
        p.publish('en')

        # Insert another page that is not the home page
        p2 = create_page(self.test_data2['title'], TEMPLATE_NAME, 'en',
                         parent=p, slug=self.test_data2['slug'], published=True,
                         reverse_id=self.test_data2['reverse_id'])
        p2.publish('en')

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
        p3.publish('en')

        # Insert another page that is not the home
        p4 = create_page(self.test_data4['title'], 'extra_context.html', 'en', parent=p)
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders4 = {}
        for placeholder in p4.placeholders.all():
            self.test_placeholders4[placeholder.slot] = placeholder
            # Insert some test plugins
        add_plugin(self.test_placeholders4['extra_context'], 'ExtraContextPlugin', 'en')
        p4.publish('en')

        # Insert another page that is not the home page
        p5 = create_page(self.test_data5['title'], TEMPLATE_NAME, 'en',
                         parent=p, slug=self.test_data5['slug'], published=True,
                         reverse_id=self.test_data5['reverse_id'])
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders5 = {}
        for placeholder in p5.placeholders.all():
            self.test_placeholders5[placeholder.slot] = placeholder
            # # Insert some test Text plugins
        add_plugin(self.test_placeholders5['sub'], 'TextPlugin', 'en',
                   body=self.test_data5['text_sub'])
        add_plugin(self.test_placeholders5['main'], 'TextPlugin', 'en',
                   body=self.test_data5['text_main'])
        p5.publish('en')

        # Insert another page that is not the home page
        p6 = create_page(self.test_data6['title'], TEMPLATE_NAME, 'en',
                         slug=self.test_data6['slug'], parent=p5,
                         reverse_id=self.test_data6['reverse_id'], published=True)
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders6 = {}
        for placeholder in p6.placeholders.all():
            self.test_placeholders6[placeholder.slot] = placeholder
            # # Insert some test Text plugins
        add_plugin(self.test_placeholders6['sub'], 'TextPlugin', 'en',
                   body=self.test_data6['text_sub'])
        p6.publish('en')

        # Reload test pages
        self.test_page = self.reload(p.publisher_public)
        self.test_page2 = self.reload(p2.publisher_public)
        self.test_page3 = self.reload(p3.publisher_public)
        self.test_page4 = self.reload(p4.publisher_public)
        self.test_page5 = self.reload(p5.publisher_public)
        self.test_page6 = self.reload(p6.publisher_public)

    def get_request(self, page, *args, **kwargs):
        request = super(RenderingTestCase, self).get_request(*args, **kwargs)
        request.current_page = page
        return request

    def strip_rendered(self, content):
        return content.strip().replace(u"\n", u"")

    @override_settings(CMS_TEMPLATES=[(TEMPLATE_NAME, '')])
    def render(self, template, page, context_vars={}):
        request = self.get_request(page)
        output = self.render_template_obj(template, context_vars, request)
        return self.strip_rendered(output)

    @override_settings(CMS_TEMPLATES=[(TEMPLATE_NAME, '')])
    def test_details_view(self):
        """
        Tests that the `detail` view is working.
        """
        response = details(self.get_request(self.test_page), '')
        response.render()
        r = self.strip_rendered(response.content.decode('utf8'))
        self.assertEqual(r, u'|' + self.test_data['text_main'] + u'|' + self.test_data['text_sub'] + u'|')

    @override_settings(
        CMS_PLUGIN_PROCESSORS=('cms.tests.test_rendering.sample_plugin_processor',),
        CMS_PLUGIN_CONTEXT_PROCESSORS=('cms.tests.test_rendering.sample_plugin_context_processor',),
    )
    def test_processors(self):
        """
        Tests that default plugin context processors are working, that plugin processors and plugin context processors
        can be defined in settings and are working and that extra plugin context processors can be passed to PluginContext.
        """
        def test_passed_plugin_context_processor(instance, placeholder, context):
            return {'test_passed_plugin_context_processor': 'test_passed_plugin_context_processor_ok'}

        t = u'{% load cms_tags %}' + \
            u'{{ plugin.counter }}|{{ plugin.instance.body }}|{{ test_passed_plugin_context_processor }}|{{ test_plugin_context_processor }}'
        instance, plugin = CMSPlugin.objects.all()[0].get_plugin_instance()
        instance.render_template = Template(t)
        context = PluginContext({'original_context_var': 'original_context_var_ok'}, instance,
                                self.test_placeholders['main'], processors=(test_passed_plugin_context_processor,))
        plugin_rendering._standard_processors = {}
        c = render_plugins((instance,), context, self.test_placeholders['main'])
        r = "".join(c)
        self.assertEqual(r, u'1|' + self.test_data[
            'text_main'] + '|test_passed_plugin_context_processor_ok|test_plugin_context_processor_ok|' +
                            self.test_data['text_main'] + '|main|original_context_var_ok|test_plugin_processor_ok|' + self.test_data[
                                'text_main'] + '|main|original_context_var_ok')
        plugin_rendering._standard_processors = {}

    def test_placeholder(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        t = u'{% load cms_tags %}' + \
            u'|{% placeholder "main" %}|{% placeholder "empty" %}'
        r = self.render(t, self.test_page)
        self.assertEqual(r, u'|' + self.test_data['text_main'] + '|')

    def test_placeholder_extra_context(self):
        t = u'{% load cms_tags %}{% placeholder "extra_context" %}'
        r = self.render(t, self.test_page4)
        self.assertEqual(r, self.test_data4['no_extra'])
        cache.clear()
        with self.settings(CMS_PLACEHOLDER_CONF=self.test_data4['placeholderconf']):
            r = self.render(t, self.test_page4)
        self.assertEqual(r, self.test_data4['extra'])

    def test_placeholder_or(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        t = u'{% load cms_tags %}' + \
            u'|{% placeholder "empty" or %}No content{% endplaceholder %}'
        r = self.render(t, self.test_page)
        self.assertEqual(r, u'|No content')

    def test_render_placeholder_tag(self):
        """
        Tests the {% render_placeholder %} templatetag.
        """
        render_placeholder_body = "I'm the render placeholder body"
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()

        add_plugin(ex1.placeholder, u"TextPlugin", u"en", body=render_placeholder_body)

        t = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_placeholder ex1.placeholder %}</h1>
<h2>{% render_placeholder ex1.placeholder as tempvar %}</h2>
<h3>{{ tempvar }}</h3>
{% endblock content %}
'''
        r = self.render(t, self.test_page, {'ex1': ex1})
        self.assertIn(
            '<h1>%s</h1>' % render_placeholder_body,
            r
        )

        self.assertIn(
            '<h2></h2>',
            r
        )

        self.assertIn(
            '<h3>%s</h3>' % render_placeholder_body,
            r
        )

    def test_render_uncached_placeholder_tag(self):
        """
        Tests the {% render_uncached_placeholder %} templatetag.
        """
        render_uncached_placeholder_body = "I'm the render uncached placeholder body"
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()

        add_plugin(ex1.placeholder, u"TextPlugin", u"en", body=render_uncached_placeholder_body)

        t = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_uncached_placeholder ex1.placeholder %}</h1>
<h2>{% render_uncached_placeholder ex1.placeholder as tempvar %}</h2>
<h3>{{ tempvar }}</h3>
{% endblock content %}
'''
        r = self.render(t, self.test_page, {'ex1': ex1})
        self.assertIn(
            '<h1>%s</h1>' % render_uncached_placeholder_body,
            r
        )
        self.assertIn(
            '<h2></h2>',
            r
        )

        self.assertIn(
            '<h3>%s</h3>' % render_uncached_placeholder_body,
            r
        )

    def test_render_uncached_placeholder_tag_no_use_cache(self):
        """
        Tests that {% render_uncached_placeholder %} does not populate cache.
        """
        render_uncached_placeholder_body = "I'm the render uncached placeholder body"
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        request = self.get_request('/')
        add_plugin(ex1.placeholder, u"TextPlugin", u"en", body=render_uncached_placeholder_body)

        template = '{% load cms_tags %}<h1>{% render_uncached_placeholder ex1.placeholder %}</h1>'

        cache_value_before = get_placeholder_cache(ex1.placeholder, 'en', 1, request)
        self.render(template, self.test_page, {'ex1': ex1})
        cache_value_after = get_placeholder_cache(ex1.placeholder, 'en', 1, request)

        self.assertEqual(cache_value_before, cache_value_after)
        self.assertIsNone(cache_value_after)

    def test_render_placeholder_tag_use_cache(self):
        """
        Tests that {% render_placeholder %} populates cache.
        """
        render_placeholder_body = "I'm the render placeholder body"
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        request = self.get_request('/')
        add_plugin(ex1.placeholder, u"TextPlugin", u"en", body=render_placeholder_body)

        template = '{% load cms_tags %}<h1>{% render_placeholder ex1.placeholder %}</h1>'

        cache_value_before = get_placeholder_cache(ex1.placeholder, 'en', 1, request)
        self.render(template, self.test_page, {'ex1': ex1})
        cache_value_after = get_placeholder_cache(ex1.placeholder, 'en', 1, request)

        self.assertNotEqual(cache_value_before, cache_value_after)
        self.assertIsNone(cache_value_before)
        self.assertIsNotNone(cache_value_after)

    def test_show_placeholder(self):
        """
        Tests the {% show_placeholder %} templatetag, using lookup by pk/dict/reverse_id and passing a Page object.
        """
        t = u'{% load cms_tags %}' + \
            u'|{% show_placeholder "main" ' + str(self.test_page.pk) + ' %}' + \
            u'|{% show_placeholder "main" test_dict %}' + \
            u'|{% show_placeholder "sub" "' + str(self.test_page.reverse_id) + '" %}' + \
            u'|{% show_placeholder "sub" test_page %}'
        r = self.render(t, self.test_page, {'test_page': self.test_page, 'test_dict': {'pk': self.test_page.pk}})
        self.assertEqual(r, (u'|' + self.test_data['text_main']) * 2 + (u'|' + self.test_data['text_sub']) * 2)

    def test_show_placeholder_extra_context(self):
        t = u'{% load cms_tags %}{% show_uncached_placeholder "extra_context" ' + str(self.test_page4.pk) + ' %}'
        r = self.render(t, self.test_page4)
        self.assertEqual(r, self.test_data4['no_extra'])
        cache.clear()
        with self.settings(CMS_PLACEHOLDER_CONF=self.test_data4['placeholderconf']):
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

    def test_show_uncached_placeholder_tag_no_use_cache(self):
        """
        Tests that {% show_uncached_placeholder %} does not populate cache.
        """
        template = '{% load cms_tags %}<h1>{% show_uncached_placeholder "sub" test_page %}</h1>'
        placeholder = self.test_page.placeholders.get(slot='sub')
        request = self.get_request(self.test_page)
        cache_value_before = get_placeholder_cache(placeholder, 'en', 1, request)
        output = self.render(template, self.test_page, {'test_page': self.test_page})
        cache_value_after = get_placeholder_cache(placeholder, 'en', 1, request)

        self.assertEqual(output, '<h1>%s</h1>' % self.test_data['text_sub'])
        self.assertEqual(cache_value_before, cache_value_after)
        self.assertIsNone(cache_value_after)

    def test_page_url_by_pk(self):
        template = u'{%% load cms_tags %%}{%% page_url %s %%}' % self.test_page2.pk
        output = self.render(template, self.test_page)
        self.assertEqual(output, self.test_page2.get_absolute_url())

    def test_page_url_by_dictionary(self):
        template = u'{% load cms_tags %}{% page_url test_dict %}'
        output = self.render(template, self.test_page, {'test_dict': {'pk': self.test_page2.pk}})
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

    def test_page_url_by_page_as(self):
        template = u'{% load cms_tags %}{% page_url test_page as test_url %}{{ test_url }}'
        output = self.render(template, self.test_page, {'test_page': self.test_page2})
        self.assertEqual(output, self.test_page2.get_absolute_url())

    #
    # To ensure compatible behaviour, test that page_url swallows any
    # Page.DoesNotExist exceptions when NOT in DEBUG mode.
    #
    @override_settings(DEBUG=False)
    def test_page_url_on_bogus_page(self):
        template = u'{% load cms_tags %}{% page_url "bogus_page" %}'
        output = self.render(template, self.test_page, {'test_page': self.test_page2})
        self.assertEqual(output, '')

    #
    # To ensure compatible behaviour, test that page_url will raise a
    # Page.DoesNotExist exception when the page argument does not eval to a
    # valid page
    #
    @override_settings(DEBUG=True)
    def test_page_url_on_bogus_page_in_debug(self):
        template = u'{% load cms_tags %}{% page_url "bogus_page" %}'
        self.assertRaises(
            Page.DoesNotExist,
            self.render,
            template,
            self.test_page,
            {'test_page': self.test_page2}
        )

    #
    # In the 'as varname' form, ensure that the tag will always swallow
    # Page.DoesNotExist exceptions both when DEBUG is False and...
    #
    @override_settings(DEBUG=False)
    def test_page_url_as_on_bogus_page(self):
        template = u'{% load cms_tags %}{% page_url "bogus_page" as test_url %}{{ test_url }}'
        output = self.render(template, self.test_page, {'test_page': self.test_page2})
        self.assertEqual(output, '')

    #
    # ...when it is True.
    #
    @override_settings(DEBUG=True)
    def test_page_url_as_on_bogus_page_in_debug(self):
        template = u'{% load cms_tags %}{% page_url "bogus_page" as test_url %}{{ test_url }}'
        output = self.render(template, self.test_page, {'test_page': self.test_page2})
        self.assertEqual(output, '')

    def test_page_attribute(self):
        """
        Tests the {% page_attribute %} templatetag, using current page, lookup by pk/dict/reverse_id and passing a Page object.
        """
        t = u'{% load cms_tags %}' + \
            u'|{% page_attribute title %}' + \
            u'{% page_attribute title as title %}' + \
            u'|{{ title }}' + \
            u'|{% page_attribute title ' + str(self.test_page2.pk) + ' %}' + \
            u'{% page_attribute title ' + str(self.test_page2.pk) + ' as title %}' + \
            u'|{{ title }}' + \
            u'|{% page_attribute title test_dict %}' + \
            u'{% page_attribute title test_dict as title %}' + \
            u'|{{ title }}' + \
            u'|{% page_attribute slug "' + str(self.test_page2.reverse_id) + '" %}' + \
            u'{% page_attribute slug "' + str(self.test_page2.reverse_id) + '" as slug %}' + \
            u'|{{ slug }}' + \
            u'|{% page_attribute slug test_page %}' + \
            u'{% page_attribute slug test_page as slug %}' + \
            u'|{{ slug }}'
        r = self.render(t, self.test_page, {'test_page': self.test_page2, 'test_dict': {'pk': self.test_page2.pk}})
        self.assertEqual(r, (u'|' + self.test_data['title']) * 2 + (u'|' + self.test_data2['title']) * 4 + (
            u'|' + self.test_data2['slug']) * 4)

    def test_inherit_placeholder(self):
        t = u'{% load cms_tags %}' + \
            u'|{% placeholder "main" inherit %}|{% placeholder "sub" %}'
        # a page whose parent has no 'main' placeholder inherits from ancestors
        r = self.render(t, self.test_page3)
        self.assertEqual(r, u'|' + self.test_data['text_main'] + '|' + self.test_data3['text_sub'])

        # a page whose parent has 'main' placeholder inherits from the parent, not ancestors
        r = self.render(t, self.test_page6)
        self.assertEqual(r, u'|' + self.test_data5['text_main'] + '|' + self.test_data6['text_sub'])

    def test_extra_context_isolation(self):
        with ChangeModel(self.test_page, template='extra_context.html'):
            response = self.client.get(self.test_page.get_absolute_url())
            # only test the swallower context, other items in response.context are throwaway
            # contexts used for rendering templates fragments and templatetags
            self.assertFalse('extra_width' in response.context[0])

    def test_render_placeholder_toolbar(self):
        placeholder = Placeholder()
        placeholder.slot = 'test'
        placeholder.pk = placeholder.id = 99
        request = AttributeObject(
            GET={'language': 'en'},
            session={},
            path='/',
            user=self.test_user,
            current_page=None,
            method='GET',
        )
        request.toolbar = CMSToolbar(request)

        context = SekizaiContext()
        context['request'] = request

        classes = [
            "cms-placeholder-%s" % placeholder.pk,
            'cms-placeholder',
        ]
        output = render_placeholder_toolbar(placeholder, context, 'test', 'en')
        for cls in classes:
            self.assertTrue(cls in output, '%r is not in %r' % (cls, output))
