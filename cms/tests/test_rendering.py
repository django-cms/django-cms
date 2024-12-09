from django.core.cache import cache
from django.http.response import Http404
from django.test.utils import override_settings
from django.urls import reverse
from sekizai.context import SekizaiContext

from cms import plugin_rendering
from cms.api import add_plugin, create_page
from cms.cache.placeholder import get_placeholder_cache
from cms.models import EmptyPageContent, Page, Placeholder
from cms.plugin_rendering import PluginContext
from cms.test_utils.project.placeholderapp.models import Example1
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.toolbar.toolbar import CMSToolbar
from cms.toolbar.utils import get_object_edit_url
from cms.views import details

TEMPLATE_NAME = 'tests/rendering/base.html'
INHERIT_TEMPLATE_NAME = 'tests/rendering/inherit.html'
INHERIT_WITH_OR_TEMPLATE_NAME = 'tests/rendering/inherit_with_or.html'


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
    CMS_TEMPLATES=[
        (TEMPLATE_NAME, TEMPLATE_NAME),
        ('extra_context.html', 'extra_context.html')
    ],
)
class RenderingEmptyTestCase(CMSTestCase):
    def setUp(self):
        super().setUp()
        self.test_data = {
            'title': 'RenderingTestCase-title',
            'slug': 'renderingtestcase-slug',
            'reverse_id': 'renderingtestcase-reverse-id',
        }

        self.user = self.get_superuser()
        self.client.force_login(self.user)
        self.page = create_page(
            self.test_data['title'], TEMPLATE_NAME, 'en',
            slug=self.test_data['slug'], created_by=self.user,
            reverse_id=self.test_data['reverse_id']
        )
        # we need an empty pagecontent for this.
        self.page.pagecontent_set.all().delete()

    def test_page_with_empty_pagecontent(self):
        """
        A page with EmptyPageContent except root returns 404 when you try to view it.
        """
        page_content = self.page.get_content_obj('en', force_reload=True)
        self.assertEqual(isinstance(page_content, EmptyPageContent), True)

        with self.assertRaises(Http404):
            path = self.page.get_path('en')
            request = self.get_request(path=path, page=self.page)
            details(request, slug=path)

    def test_page_with_empty_pagecontent_for_root_url(self):
        """
        The root page with EmptyPageContent redirects to PageContent's changelist
        """
        page_content = self.page.get_content_obj('en', force_reload=True)
        self.assertEqual(isinstance(page_content, EmptyPageContent), True)

        request = self.get_request(path='/en/', page=self.page)
        response = details(request, slug=self.page.get_path('en'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin:cms_pagecontent_changelist'))


@override_settings(
    CMS_TEMPLATES=[
        (TEMPLATE_NAME, TEMPLATE_NAME),
        (INHERIT_TEMPLATE_NAME, INHERIT_TEMPLATE_NAME),
        (INHERIT_WITH_OR_TEMPLATE_NAME, INHERIT_WITH_OR_TEMPLATE_NAME),
        ('extra_context.html', 'extra_context.html')
    ],
)
class RenderingTestCase(CMSTestCase):

    def setUp(self):
        super().setUp()
        self.test_user = self.get_superuser()

        with self.login_user_context(self.test_user):
            self.test_data = {
                'title': 'RenderingTestCase-title',
                'slug': 'renderingtestcase-slug',
                'reverse_id': 'renderingtestcase-reverse-id',
                'text_main': 'RenderingTestCase-main',
                'text_sub': 'RenderingTestCase-sub',
            }
            self.test_data2 = {
                'title': 'RenderingTestCase-title2',
                'slug': 'RenderingTestCase-slug2',
                'reverse_id': 'renderingtestcase-reverse-id2',
            }
            self.test_data3 = {
                'title': 'RenderingTestCase-title3',
                'slug': 'RenderingTestCase-slug3',
                'reverse_id': 'renderingtestcase-reverse-id3',
                'text_sub': 'RenderingTestCase-sub3',
            }
            self.test_data4 = {
                'title': 'RenderingTestCase-title3',
                'no_extra': 'no extra var!',
                'placeholderconf': {'extra_context': {'extra_context': {'extra_var': 'found extra var'}}},
                'extra': 'found extra var',
            }
            self.test_data5 = {
                'title': 'RenderingTestCase-title5',
                'slug': 'RenderingTestCase-slug5',
                'reverse_id': 'renderingtestcase-reverse-id5',
                'text_main': 'RenderingTestCase-main-page5',
                'text_sub': 'RenderingTestCase-sub5',
            }
            self.test_data6 = {
                'title': 'RenderingTestCase-title6',
                'slug': 'RenderingTestCase-slug6',
                'reverse_id': 'renderingtestcase-reverse-id6',
                'text_sub': 'RenderingTestCase-sub6',
            }
            self.test_data7 = {
                'title': 'RenderingTestCase-title7',
                'slug': 'RenderingTestCase-slug7',
                'reverse_id': 'renderingtestcase-reverse-id7',
                'text_sub': 'RenderingTestCase-sub7',
            }
            self.test_data8 = {
                'title': 'RenderingTestCase-title8',
                'slug': 'RenderingTestCase-slug8',
                'reverse_id': 'renderingtestcase-reverse-id8',
                'text_sub': 'RenderingTestCase-sub8',
            }
            self.test_data9 = {
                'title': 'RenderingTestCase-title9',
                'slug': 'RenderingTestCase-slug9',
                'reverse_id': 'renderingtestcase-reverse-id9',
                'text_sub': 'RenderingTestCase-sub9',
            }
            self.test_data10 = {
                'title': 'RenderingTestCase-title10',
                'slug': 'RenderingTestCase-slug10',
                'reverse_id': 'renderingtestcase-reverse-id10',
                'text_sub': 'RenderingTestCase-sub10',
            }
            self.insert_test_content()

    def insert_test_content(self):
        # Insert a page
        p = create_page(self.test_data['title'], TEMPLATE_NAME, 'en',
                        slug=self.test_data['slug'], created_by=self.test_user,
                        reverse_id=self.test_data['reverse_id'])
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders = {}
        for placeholder in p.get_placeholders('en'):
            self.test_placeholders[placeholder.slot] = placeholder
            # Insert some test Text plugins
        add_plugin(self.test_placeholders['main'], 'TextPlugin', 'en',
                   body=self.test_data['text_main'])
        add_plugin(self.test_placeholders['sub'], 'TextPlugin', 'en',
                   body=self.test_data['text_sub'])

        # Insert another page that is not the home page
        p2 = create_page(self.test_data2['title'], INHERIT_TEMPLATE_NAME, 'en',
                         parent=p, slug=self.test_data2['slug'],
                         reverse_id=self.test_data2['reverse_id'])

        # Insert another page that is not the home page
        p3 = create_page(self.test_data3['title'], INHERIT_TEMPLATE_NAME, 'en',
                         slug=self.test_data3['slug'], parent=p2,
                         reverse_id=self.test_data3['reverse_id'])
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders3 = {}
        for placeholder in p3.get_placeholders('en'):
            self.test_placeholders3[placeholder.slot] = placeholder
            # # Insert some test Text plugins
        add_plugin(self.test_placeholders3['sub'], 'TextPlugin', 'en', body=self.test_data3['text_sub'])

        # Insert another page that is not the home
        p4 = create_page(self.test_data4['title'], 'extra_context.html', 'en', parent=p)
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders4 = {}
        for placeholder in p4.get_placeholders('en'):
            self.test_placeholders4[placeholder.slot] = placeholder
            # Insert some test plugins
        add_plugin(self.test_placeholders4['extra_context'], 'ExtraContextPlugin', 'en')

        # Insert another page that is not the home page
        p5 = create_page(
            self.test_data5['title'], INHERIT_TEMPLATE_NAME, 'en',
            parent=p, slug=self.test_data5['slug'],
            reverse_id=self.test_data5['reverse_id']
        )
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders5 = {}
        for placeholder in p5.get_placeholders('en'):
            self.test_placeholders5[placeholder.slot] = placeholder
            # # Insert some test Text plugins
        add_plugin(self.test_placeholders5['sub'], 'TextPlugin', 'en', body=self.test_data5['text_sub'])
        add_plugin(self.test_placeholders5['main'], 'TextPlugin', 'en', body=self.test_data5['text_main'])

        # Insert another page that is not the home page
        p6 = create_page(
            self.test_data6['title'], INHERIT_TEMPLATE_NAME, 'en',
            slug=self.test_data6['slug'], parent=p5,
            reverse_id=self.test_data6['reverse_id']
        )
        # Placeholders have been inserted on post_save signal:
        self.test_placeholders6 = {}
        for placeholder in p6.get_placeholders('en'):
            self.test_placeholders6[placeholder.slot] = placeholder
            # # Insert some test Text plugins
        add_plugin(self.test_placeholders6['sub'], 'TextPlugin', 'en', body=self.test_data6['text_sub'])
        p7 = create_page(
            self.test_data7['title'], INHERIT_TEMPLATE_NAME, 'en',
            slug=self.test_data7['slug'], parent=p6,
            reverse_id=self.test_data7['reverse_id']
        )
        p8 = create_page(
            self.test_data8['title'], INHERIT_WITH_OR_TEMPLATE_NAME, 'en',
            slug=self.test_data8['slug'], parent=p7,
            reverse_id=self.test_data8['reverse_id']
        )
        p9 = create_page(
            self.test_data9['title'], INHERIT_WITH_OR_TEMPLATE_NAME, 'en',
            slug=self.test_data9['slug'],
            reverse_id=self.test_data9['reverse_id']
        )
        p10 = create_page(
            self.test_data10['title'], INHERIT_WITH_OR_TEMPLATE_NAME, 'en',
            slug=self.test_data10['slug'], parent=p9,
            reverse_id=self.test_data10['reverse_id'])

        # Reload test pages
        self.test_page = self.reload(p)
        self.test_page2 = self.reload(p2)
        self.test_page3 = self.reload(p3)
        self.test_page4 = self.reload(p4)
        self.test_page5 = self.reload(p5)
        self.test_page6 = self.reload(p6)
        self.test_page7 = self.reload(p7)
        self.test_page8 = self.reload(p8)
        self.test_page9 = self.reload(p9)
        self.test_page10 = self.reload(p10)

    def strip_rendered(self, content):
        return content.strip().replace("\n", "")

    @override_settings(CMS_TEMPLATES=[(TEMPLATE_NAME, '')])
    def render(self, page, template=None, context_vars=None, request=None):
        if request is None:
            request = self.get_request(page=page)
            request.toolbar = CMSToolbar(request)

        if context_vars is None:
            context_vars = {}

        if template is None:
            template = page.get_template()
            template_obj = self.get_template(template)
            output = template_obj.render(context_vars, request)
        else:
            output = self.render_template_obj(template, context_vars, request)
        return self.strip_rendered(output)

    @override_settings(CMS_TEMPLATES=[(TEMPLATE_NAME, '')])
    def test_details_view(self):
        """
        Tests that the `detail` view is working.
        """
        response = details(self.get_request(page=self.test_page), self.test_page.get_path('en'))
        response.render()
        r = self.strip_rendered(response.content.decode('utf8'))
        self.assertEqual(r, '|' + self.test_data['text_main'] + '|' + self.test_data['text_sub'] + '|')

    def test_getting_placeholders(self):
        """ContentRenderer._get_content_object uses toolbar to return placeholders of a page"""
        request = self.get_request(page=self.test_page)
        request.toolbar = CMSToolbar(request)
        wrong_content_obj = self.test_page2.get_content_obj("en")
        wrong_content_obj.page = self.test_page
        request.toolbar.set_object(wrong_content_obj)
        content_renderer = self.get_content_renderer(request)
        placeholders = content_renderer._get_content_object(self.test_page)
        wrong_content_obj.page = self.test_page2

        self.assertEqual(len(placeholders), 2)

    @override_settings(
        CMS_PLUGIN_PROCESSORS=('cms.tests.test_rendering.sample_plugin_processor',),
        CMS_PLUGIN_CONTEXT_PROCESSORS=('cms.tests.test_rendering.sample_plugin_context_processor',),
    )
    def test_processors(self):
        """
        Tests that plugin processors and plugin context processors can be defined
        in settings and are working and that extra plugin context processors can be
        passed to PluginContext.
        """
        from djangocms_text_ckeditor.cms_plugins import TextPlugin

        from cms.plugin_pool import plugin_pool

        instance = self.test_placeholders['main'].get_plugins('en').first().get_bound_plugin()

        load_from_string = self.load_template_from_string

        @plugin_pool.register_plugin
        class ProcessorTestPlugin(TextPlugin):
            name = "Test Plugin"

            def get_render_template(self, context, instance, placeholder):
                t = '{% load cms_tags %}' + \
                    '{{ body }}|test_passed_plugin_context_processor_ok|' \
                    '{{ test_plugin_context_processor }}'
                return load_from_string(t)

        def test_passed_plugin_context_processor(instance, placeholder, context):
            return {'test_passed_plugin_context_processor': 'test_passed_plugin_context_processor_ok'}

        instance.plugin_type = 'ProcessorTestPlugin'
        instance._inst = instance

        context = PluginContext(
            {'original_context_var': 'original_context_var_ok', "request": None},
            instance,
            self.test_placeholders['main'], processors=(test_passed_plugin_context_processor,)
        )
        plugin_rendering._standard_processors = {}

        content_renderer = self.get_content_renderer()
        r = content_renderer.render_plugin(instance, context, self.test_placeholders['main'])
        expected = (
            f"{self.test_data['text_main']}|test_passed_plugin_context_processor_ok|test_plugin_context_processor_ok|"
            f"{self.test_data['text_main']}|main|original_context_var_ok|test_plugin_processor_ok|"
            f"{self.test_data['text_main']}|main|original_context_var_ok"
        )
        self.assertEqual(r, expected)
        plugin_rendering._standard_processors = {}

    def test_placeholder(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        r = self.render(self.test_page)
        self.assertEqual(r, '|' + self.test_data['text_main'] + '|' + self.test_data['text_sub'] + '|')

    def test_placeholder_extra_context(self):
        t = '{% load cms_tags %}{% placeholder "extra_context" %}'
        r = self.render(self.test_page4, template=t)
        self.assertEqual(r, self.test_data4['no_extra'])
        cache.clear()
        with self.settings(CMS_PLACEHOLDER_CONF=self.test_data4['placeholderconf']):
            r = self.render(self.test_page4, template=t)
        self.assertEqual(r, self.test_data4['extra'])

    def test_placeholder_or(self):
        """
        Tests the {% placeholder %} templatetag.
        """
        t = '{% load cms_tags %}' + \
            '|{% placeholder "empty" or %}No content{% endplaceholder %}'
        r = self.render(self.test_page, template=t)
        self.assertEqual(r, '|No content')

    def test_placeholder_or_in_edit_mode(self):
        """
        Tests the {% placeholder or %} templatetag in edit mode.
        """
        t = '{% load cms_tags %}' + \
            '|{% placeholder "empty" or %}No content{% endplaceholder %}'
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            endpoint = self.test_page.get_absolute_url() + '?edit'
            request = self.get_request(endpoint, page=self.test_page)
            request.session['cms_edit'] = True
            request.toolbar = CMSToolbar(request)

        renderer = self.get_content_renderer(request)
        context = SekizaiContext()
        context['cms_content_renderer'] = renderer
        placeholder = self.test_page.get_placeholders('en').get(slot='empty')
        expected = renderer.render_placeholder(
            placeholder,
            context=context,
            language='en',
            page=self.test_page,
            editable=True,
        )
        expected = f'|{expected}No content'
        rendered = self.render(self.test_page, template=t, request=request)
        self.assertEqual(rendered, self.strip_rendered(expected))

    def test_render_placeholder_tag(self):
        """
        Tests the {% render_placeholder %} templatetag.
        """
        render_placeholder_body = "I'm the render placeholder body"
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()

        add_plugin(ex1.placeholder, "TextPlugin", "en", body=render_placeholder_body)

        t = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_placeholder ex1.placeholder %}</h1>
<h2>{% render_placeholder ex1.placeholder as tempvar %}</h2>
<h3>{{ tempvar }}</h3>
{% endblock content %}
'''
        r = self.render(self.test_page, template=t, context_vars={'ex1': ex1})
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

        add_plugin(ex1.placeholder, "TextPlugin", "en", body=render_uncached_placeholder_body)

        t = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_uncached_placeholder ex1.placeholder %}</h1>
<h2>{% render_uncached_placeholder ex1.placeholder as tempvar %}</h2>
<h3>{{ tempvar }}</h3>
{% endblock content %}
'''
        r = self.render(self.test_page, template=t, context_vars={'ex1': ex1})
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
        add_plugin(ex1.placeholder, "TextPlugin", "en", body=render_uncached_placeholder_body)

        template = '{% load cms_tags %}<h1>{% render_uncached_placeholder ex1.placeholder %}</h1>'

        cache_value_before = get_placeholder_cache(ex1.placeholder, 'en', 1, request)
        self.render(self.test_page, template, {'ex1': ex1})
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
        add_plugin(ex1.placeholder, "TextPlugin", "en", body=render_placeholder_body)

        template = '{% load cms_tags %}<h1>{% render_placeholder ex1.placeholder %}</h1>'

        cache_value_before = get_placeholder_cache(ex1.placeholder, 'en', 1, request)
        self.render(self.test_page, template, {'ex1': ex1})
        cache_value_after = get_placeholder_cache(ex1.placeholder, 'en', 1, request)

        self.assertNotEqual(cache_value_before, cache_value_after)
        self.assertIsNone(cache_value_before)
        self.assertIsNotNone(cache_value_after)

    def test_show_placeholder(self):
        """
        Tests the {% show_placeholder %} templatetag, using lookup by pk/dict/reverse_id and passing a Page object.
        """
        t = '{% load cms_tags %}' + \
            '|{% show_placeholder "main" ' + str(self.test_page.pk) + ' %}' + \
            '|{% show_placeholder "main" test_dict %}' + \
            '|{% show_placeholder "sub" "' + str(self.test_page.reverse_id) + '" %}' + \
            '|{% show_placeholder "sub" test_page %}'
        r = self.render(
            self.test_page,
            template=t,
            context_vars={'test_page': self.test_page, 'test_dict': {'pk': self.test_page.pk}}
        )
        self.assertEqual(r, ('|' + self.test_data['text_main']) * 2 + ('|' + self.test_data['text_sub']) * 2)

    def test_show_placeholder_extra_context(self):
        t = '{% load cms_tags %}{% show_uncached_placeholder "extra_context" ' + str(self.test_page4.pk) + ' %}'
        r = self.render(self.test_page4, template=t)
        self.assertEqual(r, self.test_data4['no_extra'])
        cache.clear()
        with self.settings(CMS_PLACEHOLDER_CONF=self.test_data4['placeholderconf']):
            r = self.render(self.test_page4, template=t)
            self.assertEqual(r, self.test_data4['extra'])

    def test_show_uncached_placeholder_by_pk(self):
        """
        Tests the {% show_uncached_placeholder %} templatetag, using lookup by pk.
        """
        template = '{%% load cms_tags %%}{%% show_uncached_placeholder "main" %s %%}' % self.test_page.pk
        output = self.render(self.test_page, template)
        self.assertEqual(output, self.test_data['text_main'])

    def test_show_uncached_placeholder_by_lookup_dict(self):
        template = '{% load cms_tags %}{% show_uncached_placeholder "main" test_dict %}'
        output = self.render(self.test_page, template, {'test_dict': {'pk': self.test_page.pk}})
        self.assertEqual(output, self.test_data['text_main'])

    def test_show_uncached_placeholder_by_reverse_id(self):
        template = '{%% load cms_tags %%}{%% show_uncached_placeholder "sub" "%s" %%}' % self.test_page.reverse_id
        output = self.render(self.test_page, template)
        self.assertEqual(output, self.test_data['text_sub'])

    def test_show_uncached_placeholder_by_page(self):
        template = '{% load cms_tags %}{% show_uncached_placeholder "sub" test_page %}'
        output = self.render(self.test_page, template, {'test_page': self.test_page})
        self.assertEqual(output, self.test_data['text_sub'])

    def test_show_uncached_placeholder_tag_no_use_cache(self):
        """
        Tests that {% show_uncached_placeholder %} does not populate cache.
        """
        template = '{% load cms_tags %}<h1>{% show_uncached_placeholder "sub" test_page %}</h1>'
        placeholder = self.test_page.get_placeholders('en').get(slot='sub')
        request = self.get_request(page=self.test_page)
        cache_value_before = get_placeholder_cache(placeholder, 'en', 1, request)
        output = self.render(self.test_page, template, {'test_page': self.test_page})
        cache_value_after = get_placeholder_cache(placeholder, 'en', 1, request)

        self.assertEqual(output, '<h1>%s</h1>' % self.test_data['text_sub'])
        self.assertEqual(cache_value_before, cache_value_after)
        self.assertIsNone(cache_value_after)

    def test_page_url_by_pk(self):
        template = '{%% load cms_tags %%}{%% page_url %s %%}' % self.test_page2.pk
        output = self.render(self.test_page, template)
        self.assertEqual(output, self.test_page2.get_absolute_url())

    def test_page_url_by_dictionary(self):
        template = '{% load cms_tags %}{% page_url test_dict %}'
        output = self.render(self.test_page, template, {'test_dict': {'pk': self.test_page2.pk}})
        self.assertEqual(output, self.test_page2.get_absolute_url())

    def test_page_url_by_reverse_id(self):
        template = '{%% load cms_tags %%}{%% page_url "%s" %%}' % self.test_page2.reverse_id
        output = self.render(self.test_page, template)
        self.assertEqual(output, self.test_page2.get_absolute_url())

    def test_page_url_by_reverse_id_not_on_a_page(self):
        template = '{%% load cms_tags %%}{%% page_url "%s" %%}' % self.test_page2.reverse_id
        output = self.render(None, template)
        self.assertEqual(output, self.test_page2.get_absolute_url())

    def test_page_url_by_page(self):
        template = '{% load cms_tags %}{% page_url test_page %}'
        output = self.render(self.test_page, template, {'test_page': self.test_page2})
        self.assertEqual(output, self.test_page2.get_absolute_url())

    def test_page_url_by_page_as(self):
        template = '{% load cms_tags %}{% page_url test_page as test_url %}{{ test_url }}'
        output = self.render(self.test_page, template, {'test_page': self.test_page2})
        self.assertEqual(output, self.test_page2.get_absolute_url())

    #
    # To ensure compatible behaviour, test that page_url swallows any
    # Page.DoesNotExist exceptions when NOT in DEBUG mode.
    #
    @override_settings(DEBUG=False)
    def test_page_url_on_bogus_page(self):
        template = '{% load cms_tags %}{% page_url "bogus_page" %}'
        output = self.render(self.test_page, template, {'test_page': self.test_page2})
        self.assertEqual(output, '')

    #
    # To ensure compatible behaviour, test that page_url will raise a
    # Page.DoesNotExist exception when the page argument does not eval to a
    # valid page
    #
    @override_settings(DEBUG=True)
    def test_page_url_on_bogus_page_in_debug(self):
        template = '{% load cms_tags %}{% page_url "bogus_page" %}'
        self.assertRaises(
            Page.DoesNotExist,
            self.render,
            self.test_page,
            template,
            {'test_page': self.test_page2}
        )

    #
    # In the 'as varname' form, ensure that the tag will always swallow
    # Page.DoesNotExist exceptions both when DEBUG is False and...
    #
    @override_settings(DEBUG=False)
    def test_page_url_as_on_bogus_page(self):
        template = '{% load cms_tags %}{% page_url "bogus_page" as test_url %}{{ test_url }}'
        output = self.render(self.test_page, template, {'test_page': self.test_page2})
        self.assertEqual(output, '')

    #
    # ...when it is True.
    #
    @override_settings(DEBUG=True)
    def test_page_url_as_on_bogus_page_in_debug(self):
        template = '{% load cms_tags %}{% page_url "bogus_page" as test_url %}{{ test_url }}'
        output = self.render(self.test_page, template, {'test_page': self.test_page2})
        self.assertEqual(output, '')

    def test_page_attribute(self):
        """
        Tests the {% page_attribute %} templatetag, using current page, lookup by pk/dict/reverse_id and passing a
        Page object.
        """
        t = '{% load cms_tags %}' + \
            '|{% page_attribute title %}' + \
            '{% page_attribute title as title %}' + \
            '|{{ title }}' + \
            '|{% page_attribute title ' + str(self.test_page2.pk) + ' %}' + \
            '{% page_attribute title ' + str(self.test_page2.pk) + ' as title %}' + \
            '|{{ title }}' + \
            '|{% page_attribute title test_dict %}' + \
            '{% page_attribute title test_dict as title %}' + \
            '|{{ title }}' + \
            '|{% page_attribute slug "' + str(self.test_page2.reverse_id) + '" %}' + \
            '{% page_attribute slug "' + str(self.test_page2.reverse_id) + '" as slug %}' + \
            '|{{ slug }}' + \
            '|{% page_attribute slug test_page %}' + \
            '{% page_attribute slug test_page as slug %}' + \
            '|{{ slug }}'
        r = self.render(
            self.test_page,
            template=t,
            context_vars={'test_page': self.test_page2, 'test_dict': {'pk': self.test_page2.pk}}
        )
        self.assertEqual(r, ('|' + self.test_data['title']) * 2 + ('|' + self.test_data2['title']) * 4 + (
            '|' + self.test_data2['slug']) * 4)

    def test_inherit_placeholder(self):
        # a page whose parent has no 'main' placeholder inherits from ancestors
        r = self.render(self.test_page3)
        self.assertEqual(r, '|' + self.test_data['text_main'] + '|' + self.test_data3['text_sub'])

        # a page whose parent has 'main' placeholder inherits from the parent, not ancestors
        r = self.render(self.test_page6)
        self.assertEqual(r, '|' + self.test_data5['text_main'] + '|' + self.test_data6['text_sub'])

    def test_inherit_placeholder_with_cache(self):
        expected_6 = '|' + self.test_data5['text_main'] + '|' + self.test_data6['text_sub']
        expected_7 = '|' + self.test_data5['text_main'] + '|'
        # Render the top-most page
        # This will cache its contents
        self.render(self.test_page)
        # Render the parent page
        # This will cache its contents
        self.render(self.test_page5)
        # Render the target page
        # This should use the cached parent page content
        self.assertEqual(self.render(self.test_page6), expected_6)
        self.assertEqual(self.render(self.test_page7), expected_7)

        self.render(self.test_page9)
        # This should use the cached parent page content
        self.assertEqual(self.render(self.test_page10), '|<p>Ultimate fallback</p>|')

    def test_inherit_placeholder_with_or(self):
        # Tests that the "or" statement used in a {% placeholder %}
        # declaration is used as the last fallback when inheritance
        # fails to find content.
        expected_8 = '|' + self.test_data5['text_main'] + '|'
        self.assertEqual(self.render(self.test_page8), expected_8)

        expected_10 = '|<p>Ultimate fallback</p>|'
        self.assertEqual(self.render(self.test_page10), expected_10)

    def test_inherit_placeholder_override(self):
        # Tests that the user can override the inherited content
        # in a placeholder by adding plugins to the inherited placeholder.
        # a page whose parent has 'main' placeholder inherits from the parent, not ancestors
        r = self.render(self.test_page5)
        self.assertEqual(r, '|' + self.test_data5['text_main'] + '|' + self.test_data5['text_sub'])

    @override_settings(CMS_PLACEHOLDER_CONF={None: {'language_fallback': False}})
    def test_inherit_placeholder_queries(self):
        with self.assertNumQueries(FuzzyInt(6, 10)):
            r = self.render(self.test_page2)
            self.assertEqual(r, '|' + self.test_data['text_main'] + '|')

    def test_render_placeholder_toolbar(self):
        placeholder = Placeholder()
        placeholder.slot = 'test'
        placeholder.pk = placeholder.id = 99

        with self.login_user_context(self.get_superuser()):
            page_content = self.get_pagecontent_obj(self.test_page)
            request = self.get_request(get_object_edit_url(page_content))
            request.session = {}
            request.toolbar = CMSToolbar(request)
            renderer = self.get_content_renderer(request)
            context = SekizaiContext()
            context['request'] = request

        classes = [
            "cms-placeholder-%s" % placeholder.pk,
            'cms-placeholder',
        ]
        output = renderer.render_placeholder(placeholder, context, 'en', editable=True)

        for cls in classes:
            self.assertTrue(cls in output, '%r is not in %r' % (cls, output))

    def test_render_plugin_toolbar_markup(self):
        """
        Ensures that the edit-mode markup is correct
        """
        page = self.test_page
        placeholder = page.get_placeholders('en').get(slot='main')
        parent_plugin = add_plugin(placeholder, 'SolarSystemPlugin', 'en')
        child_plugin_1 = add_plugin(placeholder, 'PlanetPlugin', 'en', target=parent_plugin)
        child_plugin_2 = add_plugin(placeholder, 'PlanetPlugin', 'en', target=parent_plugin)
        parent_plugin.child_plugin_instances = [
            child_plugin_1,
            child_plugin_2,
        ]
        plugins = [
            parent_plugin,
            child_plugin_1,
            child_plugin_2,
        ]

        with self.login_user_context(self.get_superuser()):
            page_content = self.get_pagecontent_obj(page)
            request = self.get_request(get_object_edit_url(page_content))
            request.session = {}
            request.toolbar = CMSToolbar(request)
            context = SekizaiContext()
            context['request'] = request
            content_renderer = request.toolbar.get_content_renderer()
            output = content_renderer.render_plugin(
                instance=parent_plugin,
                context=context,
                placeholder=placeholder,
                editable=True,
            )
            tag_format = '<template class="cms-plugin cms-plugin-start cms-plugin-{}">'

        for plugin in plugins:
            start_tag = tag_format.format(plugin.pk)
            self.assertIn(start_tag, output)
