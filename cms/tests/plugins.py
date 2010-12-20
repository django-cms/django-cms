# -*- coding: utf-8 -*-
from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.models import Page, Title, Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.plugins.link.models import Link
from cms.plugins.text.models import Text
from cms.plugins.text.utils import plugin_tags_to_id_list, plugin_tags_to_admin_html
from cms.plugins.googlemap.models import GoogleMap
from cms.plugins.inherit.models import InheritPagePlaceholder
from cms.plugins.file.models import File

from cms.tests.base import CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_ADD, \
    URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT, URL_CMS_PAGE_CHANGE, \
    URL_CMS_PLUGIN_REMOVE
    
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.template import TemplateDoesNotExist, RequestContext
from django.forms.widgets import Media
from django.core.files.uploadedfile import SimpleUploadedFile

from testapp.pluginapp.models import Article, Section
from testapp.pluginapp.plugins.manytomany_rel.models import ArticlePluginModel

class DumbFixturePlugin(CMSPluginBase):
    model = CMSPlugin
    name = "Dumb Test Plugin. It does nothing."
    render_template = ""
    admin_preview = False

    def render(self, context, instance, placeholder):
        return context

class PluginsTestBaseCase(CMSTestCase):

    def setUp(self):
        self.super_user = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        self.super_user.set_password("test")
        self.super_user.save()
        
        self.slave = User(username="slave", is_staff=True, is_active=True, is_superuser=False)
        self.slave.set_password("slave")
        self.slave.save()
        
        self.login_user(self.super_user)

        self.FIRST_LANG = settings.LANGUAGES[0][0]
        self.SECOND_LANG = settings.LANGUAGES[1][0]
        
# REFACTOR - the publish and appove methods exist in this file and in permmod.py - should they be in base?
    def publish_page(self, page, approve=False, user=None, published_check=True):
        if user:
            self.login_user(user)

        # publish / approve page by master
        response = self.client.post(URL_CMS_PAGE + "%d/change-status/" % page.pk, {1 :1})
        self.assertEqual(response.status_code, 200)

        if not approve:
            return self.reload_page(page)

        # approve
        page = self.approve_page(page)

        if published_check:
            # must have public object now
            assert(page.publisher_public)
            # and public object must be published
            assert(page.publisher_public.published)

        return page

    def approve_page(self, page):
        response = self.client.get(URL_CMS_PAGE + "%d/approve/" % page.pk)
        self.assertRedirects(response, URL_CMS_PAGE)
        # reload page
        return self.reload_page(page)
        
    def get_request(self, *args, **kwargs):
        request = super(PluginsTestBaseCase, self).get_request(*args, **kwargs)
        request.placeholder_media = Media()
        return request
        
class PluginsTestCase(PluginsTestBaseCase):

    def test_01_add_edit_plugin(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + response.content + "/"
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        data = {
            "body":"Hello World"
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals("Hello World", txt.body)
        
    def test_02_copy_plugins(self):
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        self.assertEquals(len(settings.LANGUAGES) > 1, True)
        page = Page.objects.all()[0]
        placeholder = page.placeholders.get(slot="body")
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':placeholder.pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        text_plugin_pk = int(response.content)
        self.assertEquals(text_plugin_pk, CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + response.content + "/"
        
        data = {
            "body":"Hello World"
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals("Hello World", txt.body)
        # add an inline link
        #/admin/cms/page/2799/edit-plugin/17570/add-plugin/
        #http://127.0.0.1/admin/cms/page/2799/edit-plugin/17570/edit-plugin/17574/?_popup=1
        add_url = '%s%s/add-plugin/' % (URL_CMS_PLUGIN_EDIT, text_plugin_pk)
        data = {
            'plugin_type': "LinkPlugin",
            "parent_id": txt.pk,
            "language": settings.LANGUAGES[0][0],
        }
        response = self.client.post(add_url, data)
        link_pk = response.content
        self.assertEqual(response.status_code, 200)
        # edit the inline link plugin
        edit_url = '%s%s/edit-plugin/%s/' % (URL_CMS_PLUGIN_EDIT, text_plugin_pk, link_pk)
        data = {
            'name': "A Link",
            'url': "http://www.divio.ch",
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CMSPlugin.objects.get(pk=link_pk).parent.pk, txt.pk)
        #create 2nd language page
        page_data['language'] = settings.LANGUAGES[1][0]
        page_data['title'] += " %s" % settings.LANGUAGES[1][0]
        response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk + "?language=%s" % settings.LANGUAGES[1][0], page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        
        self.assertEquals(CMSPlugin.objects.all().count(), 2)
        self.assertEquals(Page.objects.all().count(), 1)
        copy_data = {
            'placeholder':page.placeholders.get(slot="body").pk,
            'language':settings.LANGUAGES[1][0],
            'copy_from':settings.LANGUAGES[0][0],
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEquals(response.status_code, 200)
        self.assertEqual(response.content.count('<li '), 1)
        # assert copy success
        self.assertEquals(CMSPlugin.objects.filter(language=settings.LANGUAGES[0][0]).count(), 2)
        self.assertEquals(CMSPlugin.objects.filter(language=settings.LANGUAGES[1][0]).count(), 2)
        self.assertEquals(CMSPlugin.objects.all().count(), 4)
        # assert plugin tree
        for link in CMSPlugin.objects.filter(plugin_type="LinkPlugin"):
            self.assertNotEqual(link.parent, None)
        for text in Text.objects.all():
            self.assertEquals(text.body, "Hello World")

    def test_03_remove_plugin_before_published(self):
        """
        When removing a draft plugin we would expect the public copy of the plugin to also be removed
        """
        # add a page
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        # there should be only 1 plugin
        self.assertEquals(CMSPlugin.objects.all().count(), 1)

        # delete the plugin
        plugin_data = {
            'plugin_id': int(response.content)
        }
        remove_url = URL_CMS_PLUGIN_REMOVE
        response = self.client.post(remove_url, plugin_data)
        self.assertEquals(response.status_code, 200)
        # there should be no plugins
        self.assertEquals(0, CMSPlugin.objects.all().count())
        
    def test_04_remove_plugin_after_published(self):
        # add a page
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        plugin_id = int(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        
        # there should be only 1 plugin
        self.assertEquals(CMSPlugin.objects.all().count(), 1)
        
        # publish page
        response = self.client.post(URL_CMS_PAGE + "%d/change-status/" % page.pk, {1 :1})
        self.assertEqual(response.status_code, 200)
        
        # there should now be two plugins - 1 draft, 1 public
        self.assertEquals(CMSPlugin.objects.all().count(), 2)
        
        # delete the plugin
        plugin_data = {
            'plugin_id': plugin_id
        }
        remove_url = URL_CMS_PLUGIN_REMOVE
        response = self.client.post(remove_url, plugin_data)
        self.assertEquals(response.status_code, 200)
        
        # there should be no plugins
        self.assertEquals(CMSPlugin.objects.all().count(), 0)

    def test_05_remove_plugin_not_associated_to_page(self):
        """
        Test case for PlaceholderField
        """
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        
        # there should be only 1 plugin
        self.assertEquals(CMSPlugin.objects.all().count(), 1)
        
        ph = Placeholder(slot="subplugin")
        ph.save()
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder': ph.pk,
            'parent': int(response.content)
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        
        plugin_data = {
            'plugin_id': int(response.content)
        }
        response = response.client.post(URL_CMS_PLUGIN_REMOVE, plugin_data)
        self.assertEquals(response.status_code, 200)
        
    def test_07_register_plugin_twice_should_raise(self):
        number_of_plugins_before = len(plugin_pool.get_all_plugins())
        # The first time we register the plugin is should work
        plugin_pool.register_plugin(DumbFixturePlugin)
        # Let's add it a second time. We should catch and exception
        raised = False
        try:
            plugin_pool.register_plugin(DumbFixturePlugin)
        except PluginAlreadyRegistered:
            raised = True
        self.assertTrue(raised)
        # Let's also unregister the plugin now, and assert it's not in the 
        # pool anymore
        plugin_pool.unregister_plugin(DumbFixturePlugin)
        # Let's make sure we have the same number of plugins as before:
        number_of_plugins_after = len(plugin_pool.get_all_plugins())
        self.assertEqual(number_of_plugins_before, number_of_plugins_after)
        
    def test_08_unregister_non_existing_plugin_should_raise(self):
        number_of_plugins_before = len(plugin_pool.get_all_plugins())
        raised = False
        try:
            # There should not be such a plugin registered if the others tests
            # don't leak plugins
            plugin_pool.unregister_plugin(DumbFixturePlugin)
        except PluginNotRegistered:
            raised = True
        self.assertTrue(raised)
        # Let's count, to make sure we didn't remove a plugin accidentally.
        number_of_plugins_after = len(plugin_pool.get_all_plugins())
        self.assertEqual(number_of_plugins_before, number_of_plugins_after)
                
    def test_09_iheritplugin_media(self):
        """
        Test case for InheritPagePlaceholder
        """
        inheritfrompage = self.create_page(title='page to inherit from')
        
        body = inheritfrompage.placeholders.get(slot="body")
        
        plugin = GoogleMap(
            plugin_type='GoogleMapPlugin',
            placeholder=body, 
            position=1, 
            language=settings.LANGUAGE_CODE, lat=1, lng=1)
        plugin.insert_at(None, position='last-child', commit=True)
        
        page = self.create_page(title='inherit from page')
        
        inherited_body = page.placeholders.get(slot="body")
                
        inherit_plugin = InheritPagePlaceholder(
            plugin_type='InheritPagePlaceholderPlugin',
            placeholder=inherited_body, 
            position=1, 
            language=settings.LANGUAGE_CODE,
            from_page=inheritfrompage,
            from_language=settings.LANGUAGE_CODE)
        inherit_plugin.insert_at(None, position='last-child', commit=True)
        
        request = self.get_request()
        context = RequestContext(request, {})
        inherit_plugin.render_plugin(context, inherited_body)
        self.assertEquals(unicode(request.placeholder_media).find('maps.google.com') != -1, True)
        
    def test_10_fileplugin_icon_uppercase(self):
        page = self.create_page(title='testpage')
        body = page.placeholders.get(slot="body") 
        plugin = File(
            plugin_type='FilePlugin',
            placeholder=body,
            position=1, 
            language=settings.LANGUAGE_CODE,
        )
        plugin.file.save("UPPERCASE.JPG", SimpleUploadedFile("UPPERCASE.jpg", "content"), False)
        plugin.insert_at(None, position='last-child', commit=True)
        
        self.assertEquals(plugin.get_icon_url().find('jpg') != -1, True)

    def test_11_copy_textplugin(self):
        """
        Test that copying of textplugins replaces references to copied plugins
        """
        
        page = self.create_page()
        
        placeholder = page.placeholders.get(slot='body')
        
        plugin_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder, 
            position=1, 
            language=self.FIRST_LANG)
        plugin_base.insert_at(None, position='last-child', commit=False)
                
        plugin = Text(body='')
        plugin_base.set_base_attr(plugin)
        plugin.save()
        
        plugin_ref_1_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder, 
            position=1, 
            language=self.FIRST_LANG)
        plugin_ref_1_base.insert_at(plugin_base, position='last-child', commit=False)    
        
        plugin_ref_1 = Text(body='')
        plugin_ref_1_base.set_base_attr(plugin_ref_1)
        plugin_ref_1.save()
        
        plugin_ref_2_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder, 
            position=2, 
            language=self.FIRST_LANG)
        plugin_ref_2_base.insert_at(plugin_base, position='last-child', commit=False)    
        
        plugin_ref_2 = Text(body='')
        plugin_ref_2_base.set_base_attr(plugin_ref_2)

        plugin_ref_2.save()
        
        plugin.body = plugin_tags_to_admin_html(' {{ plugin_object %s }} {{ plugin_object %s }} ' % (str(plugin_ref_1.pk), str(plugin_ref_2.pk)))
        plugin.save()
        self.assertEquals(plugin.pk, 1)
        page_data = self.get_new_page_data()

        #create 2nd language page
        page_data.update({
            'language': self.SECOND_LANG,
            'title': "%s %s" % (page.get_title(), self.SECOND_LANG),
        })
        response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk + "?language=%s" % self.SECOND_LANG, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        
        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 3)
        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 0)
        self.assertEquals(CMSPlugin.objects.count(), 3)
        self.assertEquals(Page.objects.all().count(), 1)
        
        copy_data = {
            'placeholder': placeholder.pk,
            'language': self.SECOND_LANG,
            'copy_from': self.FIRST_LANG,
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEquals(response.status_code, 200)
        self.assertEqual(response.content.count('<li '), 3)
        # assert copy success
        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 3)
        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 3)
        self.assertEquals(CMSPlugin.objects.count(), 6)

        new_plugin = Text.objects.get(pk=6)
        self.assertEquals(plugin_tags_to_id_list(new_plugin.body), [u'4', u'5'])
        
class PluginManyToManyTestCase(PluginsTestBaseCase):

    def setUp(self):
        self.super_user = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        self.super_user.set_password("test")
        self.super_user.save()
        
        self.slave = User(username="slave", is_staff=True, is_active=True, is_superuser=False)
        self.slave.set_password("slave")
        self.slave.save()
        
        self.login_user(self.super_user)
        
        # create 3 sections
        self.sections = []
        self.section_pks = []
        for i in range(3):
            section = Section.objects.create(name="section %s" %i)
            self.sections.append(section)
            self.section_pks.append(section.pk)
        self.section_count = len(self.sections)
        # create 10 articles by section
        for section in self.sections:
            for j in range(10):
                Article.objects.create(
                    title="article %s" % j,
                    section=section
                )
        self.FIRST_LANG = settings.LANGUAGES[0][0]
        self.SECOND_LANG = settings.LANGUAGES[1][0]


    def test_01_add_plugin_with_m2m(self):
        # add a new text plugin
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        placeholder = page.placeholders.get(slot="body")
        plugin_data = {
            'plugin_type': "ArticlePlugin",
            'language': self.FIRST_LANG,
            'placeholder': placeholder.pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + response.content + "/"
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        data = {
            'title': "Articles Plugin 1",
            "sections": self.section_pks
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArticlePluginModel.objects.count(), 1)
        plugin = ArticlePluginModel.objects.all()[0]
        self.assertEquals(self.section_count, plugin.sections.count())
    
    def test_01_add_plugin_with_m2m_and_publisher(self):
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        placeholder = page.placeholders.get(slot="body")

        # add a plugin
        plugin_data = {
            'plugin_type': "ArticlePlugin",
            'language': self.FIRST_LANG,
            'placeholder': placeholder.pk,
            
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
 
        # there should be only 1 plugin
        self.assertEquals(1, CMSPlugin.objects.all().count())
        
        articles_plugin_pk = int(response.content)
        self.assertEquals(articles_plugin_pk, CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + response.content + "/"
        
        data = {
            'title': "Articles Plugin 1",
            'sections': self.section_pks
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(1, ArticlePluginModel.objects.count())
        articles_plugin = ArticlePluginModel.objects.all()[0]
        self.assertEquals(u'Articles Plugin 1', articles_plugin.title)
        self.assertEquals(self.section_count, articles_plugin.sections.count())
        
        
        # check publish box
        page = self.publish_page(page)
    
        # there should now be two plugins - 1 draft, 1 public
        self.assertEquals(2, ArticlePluginModel.objects.all().count())
        
        db_counts = [plugin.sections.count() for plugin in ArticlePluginModel.objects.all()]
        expected = [self.section_count for i in range(len(db_counts))]
        self.assertEqual(expected, db_counts)
        
        
    def test_03_copy_plugin_with_m2m(self):
        
        page = self.create_page()
        
        placeholder = page.placeholders.get(slot='body')
        
        plugin = ArticlePluginModel(
            plugin_type='ArticlePlugin',
            placeholder=placeholder, 
            position=1, 
            language=self.FIRST_LANG)
        plugin.insert_at(None, position='last-child', commit=True)
        
        edit_url = URL_CMS_PLUGIN_EDIT + str(plugin.pk) + "/"
        
        data = {
            'title': "Articles Plugin 1",
            "sections": self.section_pks
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        self.assertEqual(ArticlePluginModel.objects.count(), 1)
        
        self.assertEqual(ArticlePluginModel.objects.all()[0].sections.count(), self.section_count)
                
        page_data = self.get_new_page_data()

        #create 2nd language page
        page_data.update({
            'language': self.SECOND_LANG,
            'title': "%s %s" % (page.get_title(), self.SECOND_LANG),
        })
        response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk + "?language=%s" % self.SECOND_LANG, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        
        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 1)
        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 0)
        self.assertEquals(CMSPlugin.objects.count(), 1)
        self.assertEquals(Page.objects.all().count(), 1)
        copy_data = {
            'placeholder': placeholder.pk,
            'language': self.SECOND_LANG,
            'copy_from': self.FIRST_LANG,
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEquals(response.status_code, 200)
        self.assertEqual(response.content.count('<li '), 1)
        # assert copy success
        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 1)
        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 1)
        self.assertEquals(CMSPlugin.objects.count(), 2)
        db_counts = [plugin.sections.count() for plugin in ArticlePluginModel.objects.all()]
        expected = [self.section_count for i in range(len(db_counts))]
        self.assertEqual(expected, db_counts)
        
