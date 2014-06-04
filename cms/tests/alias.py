# -*- coding: utf-8 -*-
from cms import api
from cms.test_utils.testcases import CMSTestCase
from django.core.urlresolvers import reverse
from django.template import Template, Context


class AliasTestCase(CMSTestCase):
    def test_plugin_alias(self):
        page_en = api.create_page("PluginOrderPage", "col_two.html", "en",
                                  slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")
        text_plugin_1 = api.add_plugin(ph_en, "TextPlugin", "en", body="I'm the first")
        with self.login_user_context(self.get_superuser()):
            response = self.client.post(reverse('admin:cms_create_alias'), data={'plugin_id': text_plugin_1.pk})
            self.assertEqual(response.status_code, 200)
            response = self.client.post(reverse('admin:cms_create_alias'), data={'placeholder_id': ph_en.pk})
            self.assertEqual(response.status_code, 200)


    def test_context_menus(self):
        page_en = api.create_page("PluginOrderPage", "col_two.html", "en",
                                  slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")
        text_plugin_1 = api.add_plugin(ph_en, "TextPlugin", "en", body="I'm the first")

        class FakeRequest(object):
            current_page = page_en
            user = self.get_superuser()
            REQUEST = {'language': 'en'}
            META = {"CSRF_COOKIE_USED": True}
        request = FakeRequest()
        template = Template('{% load cms_tags %}{% extra_menu_items placeholder %}')
        context = Context({'request': request})
        context['placeholder'] = ph_en
        output = template.render(context)
        self.assertTrue(len(output), 200)
