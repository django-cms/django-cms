# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page, publish_page, add_plugin
from cms.conf.patch import post_patch_check
from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.models import Page, Placeholder
from cms.models.pluginmodel import CMSPlugin, PluginModelBase
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.plugins.file.models import File
from cms.plugins.inherit.models import InheritPagePlaceholder
from cms.plugins.link.forms import LinkForm
from cms.plugins.link.models import Link
from cms.plugins.text.models import Text
from cms.plugins.text.utils import (plugin_tags_to_id_list, 
    plugin_tags_to_admin_html)
from cms.plugins.twitter.models import TwitterRecentEntries
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PAGE, 
    URL_CMS_PAGE_ADD, URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT, URL_CMS_PAGE_CHANGE, 
    URL_CMS_PLUGIN_REMOVE)
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils.copy_plugins import copy_plugins_to
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.forms.widgets import Media
from django.test.testcases import TestCase
from project.pluginapp.models import Article, Section
from project.pluginapp.plugins.manytomany_rel.models import ArticlePluginModel
import os


from cms.admin.forms import PageForm
from cms.api import create_page
from cms.models import Page, Title
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugins.text.models import Text
from cms.sitemaps import CMSSitemap
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PAGE, 
    URL_CMS_PAGE_ADD)
from cms.test_utils.util.context_managers import (LanguageOverride, 
    SettingsOverride)
from cms.utils.page_resolver import get_page_from_request
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
import datetime
import os.path
from cms.tests.plugins import PluginsTestBaseCase



class PluginsTestCase(PluginsTestBaseCase):
   
    def test_copy_placeholder_page(self):
        #setup page 1
        templates = []
        
        page_en = create_page("Three Placeholder", "col_three.html", "en",
                           position="last-child", published=True, in_navigation=True)
        ph_one = page_en.placeholders.get(slot="col_sidebar")
        ph_two = page_en.placeholders.get(slot="col_left")
        ph_three = page_en.placeholders.get(slot="col_right")
        page_two = create_page("Three Placeholder - page 2", "col_three.html", "en",
                           position="last-child", published=True, in_navigation=True)
        #setup page 2 as copy target
        page_two.save()
        # add the text plugin
        text_plugin_en = add_plugin(ph_one, "TextPlugin", "en", body="Hello World")
        self.assertEquals(text_plugin_en.pk, CMSPlugin.objects.all()[0].pk)
        
        # add a *nested* link plugin
        link_plugin_en = add_plugin(ph_one, "LinkPlugin", "en", target=text_plugin_en,
                                 name="A Link", url="https://www.django-cms.org")
        
        # the call above to add a child makes a plugin reload required here.
        text_plugin_en = self.reload(text_plugin_en)
        
        # check the relations
        self.assertEquals(text_plugin_en.get_children().count(), 1)
        self.assertEqual(link_plugin_en.parent.pk, text_plugin_en.pk)
        page_en_text_plugin_id = text_plugin_en.pk
        nested_plugin_id =link_plugin_en.pk
        # just sanity check that so far everything went well
        # pre
        pre_add_plugin_count=CMSPlugin.objects.count()
        self.assertEqual(pre_add_plugin_count, 2)
        page_en.save()
        # load the page and check if the texts are present
         
        ###
        # add a second plugin
        text_plugin_two = add_plugin(ph_two, "TextPlugin", "en", body="A second text plugin")
        # reload the text plugin
        text_plugin_en = self.reload(text_plugin_en)
        # get link plugin from teh reloaded text 
        self.assertEquals(text_plugin_en.get_children().count(), 1)
        self.assertEqual(link_plugin_en.parent.pk, text_plugin_en.pk)
        
        link_plugin_en = text_plugin_en.get_children()[0]
        page_en_text_plugin_id = text_plugin_en.pk
        nested_plugin_id = link_plugin_en.pk
             
        
        page_en.save()
        post_add_plugin_count=CMSPlugin.objects.count()
        self.assertEqual((post_add_plugin_count >pre_add_plugin_count) , True)
        
        all_page_count=Page.objects.all().count()
        pre_copy_placeholder_count=Placeholder.objects.count()
        ###
        # 
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            self.copy_page(page_en, page_two)
        post_copy_page_plugin_count=CMSPlugin.objects.count()
        after_copy_page_count = Page.objects.all().count()
        after_copy_placeholder_count=Placeholder.objects.count()
        
        self.assertEqual((after_copy_page_count > all_page_count), True)
        self.assertEqual((post_copy_page_plugin_count > post_add_plugin_count), True)
        self.assertEqual((after_copy_placeholder_count > pre_copy_placeholder_count), True)    
        ###
        # orginal placeholder
        ###
        page_en=self.reload(page_en)
        page_en_ph_one=page_en.placeholders.get(slot="col_sidebar")
        page_en_ph_two = page_two.placeholders.get(slot="col_left")
        page_en_ph_three = page_two.placeholders.get(slot="col_right")
        
        ##
        # copied page placeholders
        ##
        page_two=self.reload(page_two)
        page_two_ph_one = page_two.placeholders.get(slot="col_sidebar")
        page_two_ph_two = page_two.placeholders.get(slot="col_left")
        page_two_ph_three = page_two.placeholders.get(slot="col_right")
#        print "placeholder ids"
#        print "copied page placeholder 1 id %s" % page_two_ph_one.pk
#        print "org    page placeholder 1 id %s" % page_en_ph_one.pk
#        print "copied page placeholder 2 id %s" % page_two_ph_two.pk
#        print "org    page placeholder 2 id %s" % page_en_ph_two.pk
#        print "copied page placeholder 3 id %s" % page_two_ph_three.pk
#        print "org    page placeholder 3 id %s" % page_en_ph_three.pk
        msg='placehoder ids copy:%s org:%s copied page %s are identical with orginal page - tree broken' % (page_two_ph_one.pk,
                                                                                                      page_en_ph_one.pk,
                                                                                                      page_two.pk)
        self.assertNotEquals(page_two_ph_one.pk,page_en_ph_one.pk,msg)
        msg='placehoder ids copy:%s org:%s copied page %s are identical with orginal page - tree broken' % (page_two_ph_two.pk,
                                                                                                      page_en_ph_two.pk,
                                                                                                      page_two.pk)
        self.assertNotEquals(page_two_ph_two.pk,page_en_ph_two.pk,msg)
        msg='placehoder ids copy:%s org:%s copied page %s are identical with orginal page - tree broken' % (page_two_ph_three.pk,
                                                                                                      page_en_ph_three.pk,
                                                                                                      page_two.pk)
        self.assertNotEquals(page_two_ph_three.pk,page_en_ph_three.pk,msg)
        
        ###
        # get teh text plugin from the copied page
        ###
        
        
        # copy the plugins to the german placeholder
#        copy_plugins_to(ph_en.cmsplugin_set.all(), ph_de, 'de')
#        
#        self.assertEqual(ph_de.cmsplugin_set.filter(parent=None).count(), 1)
#        text_plugin_de = ph_de.cmsplugin_set.get(parent=None).get_plugin_instance()[0]
#        self.assertEqual(text_plugin_de.get_children().count(), 1)
#        link_plugin_de = text_plugin_de.get_children().get().get_plugin_instance()[0]
        
        
        
        
#    def test_move_plugins_to_another_placeholder(self):
#        """
#        Test that copying plugins works as expected.
#        """
#        # create some objects
#        page_en = create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
#        #page_de = create_page("CopyPluginTestPage (DE)", "nav_playground.html", "de")
#        ph_en = page_en.placeholders.get(slot="body")
#        #ph_de = page_de.placeholders.get(slot="body")
#        
#        # add the text plugin
#        text_plugin_en = add_plugin(ph_en, "TextPlugin", "en", body="Hello World")
#        self.assertEquals(text_plugin_en.pk, CMSPlugin.objects.all()[0].pk)
#        
#        # add a *nested* link plugin
#        link_plugin_en = add_plugin(ph_en, "LinkPlugin", "en", target=text_plugin_en,
#                                 name="A Link", url="https://www.django-cms.org")
#        
#        # the call above to add a child makes a plugin reload required here.
#        text_plugin_en = self.reload(text_plugin_en)
#        
#        # check the relations
#        self.assertEquals(text_plugin_en.get_children().count(), 1)
#        self.assertEqual(link_plugin_en.parent.pk, text_plugin_en.pk)
#        
#        # just sanity check that so far everything went well
#        self.assertEqual(CMSPlugin.objects.count(), 2)
#        
#        # copy the plugins to the german placeholder
#        copy_plugins_to(ph_en.cmsplugin_set.all(), ph_de, 'de')
#        
#        self.assertEqual(ph_de.cmsplugin_set.filter(parent=None).count(), 1)
#        text_plugin_de = ph_de.cmsplugin_set.get(parent=None).get_plugin_instance()[0]
#        self.assertEqual(text_plugin_de.get_children().count(), 1)
#        link_plugin_de = text_plugin_de.get_children().get().get_plugin_instance()[0]
#        
#        
#        # check we have twice as many plugins as before
#        self.assertEqual(CMSPlugin.objects.count(), 4)
#        
#        # check language plugins
#        self.assertEqual(CMSPlugin.objects.filter(language='de').count(), 2)
#        self.assertEqual(CMSPlugin.objects.filter(language='en').count(), 2)
#        
#        
#        text_plugin_en = self.reload(text_plugin_en)
#        link_plugin_en = self.reload(link_plugin_en)
#        
#        # check the relations in english didn't change
#        self.assertEquals(text_plugin_en.get_children().count(), 1)
#        self.assertEqual(link_plugin_en.parent.pk, text_plugin_en.pk)
#        
#        self.assertEqual(link_plugin_de.name, link_plugin_en.name)
#        self.assertEqual(link_plugin_de.url, link_plugin_en.url)
#        
#        self.assertEqual(text_plugin_de.body, text_plugin_en.body)
#        # now move the plugin to another placeholder
#
# 
#
#
#    def test_copy_textplugin(self):
#        """
#        Test that copying of textplugins replaces references to copied plugins
#        """
#        page = create_page("page", "nav_playground.html", "en")
#        
#        placeholder = page.placeholders.get(slot='body')
#
#        plugin_base = CMSPlugin(
#            plugin_type='TextPlugin',
#            placeholder=placeholder,
#            position=1,
#            language=self.FIRST_LANG)
#        plugin_base.insert_at(None, position='last-child', save=False)
#
#        plugin = Text(body='')
#        plugin_base.set_base_attr(plugin)
#        plugin.save()
#
#        plugin_ref_1_base = CMSPlugin(
#            plugin_type='TextPlugin',
#            placeholder=placeholder,
#            position=1,
#            language=self.FIRST_LANG)
#        plugin_ref_1_base.insert_at(plugin_base, position='last-child', save=False)
#
#        plugin_ref_1 = Text(body='')
#        plugin_ref_1_base.set_base_attr(plugin_ref_1)
#        plugin_ref_1.save()
#
#        plugin_ref_2_base = CMSPlugin(
#            plugin_type='TextPlugin',
#            placeholder=placeholder,
#            position=2,
#            language=self.FIRST_LANG)
#        plugin_ref_2_base.insert_at(plugin_base, position='last-child', save=False)
#
#        plugin_ref_2 = Text(body='')
#        plugin_ref_2_base.set_base_attr(plugin_ref_2)
#
#        plugin_ref_2.save()
#
#        plugin.body = plugin_tags_to_admin_html(' {{ plugin_object %s }} {{ plugin_object %s }} ' % (str(plugin_ref_1.pk), str(plugin_ref_2.pk)))
#        plugin.save()
#        self.assertEquals(plugin.pk, 1)
#        page_data = self.get_new_page_data()
#
#        #create 2nd language page
#        page_data.update({
#            'language': self.SECOND_LANG,
#            'title': "%s %s" % (page.get_title(), self.SECOND_LANG),
#        })
#        response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk + "?language=%s" % self.SECOND_LANG, page_data)
#        self.assertRedirects(response, URL_CMS_PAGE)
#
#        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 3)
#        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 0)
#        self.assertEquals(CMSPlugin.objects.count(), 3)
#        self.assertEquals(Page.objects.all().count(), 1)
#
#        copy_data = {
#            'placeholder': placeholder.pk,
#            'language': self.SECOND_LANG,
#            'copy_from': self.FIRST_LANG,
#        }
#        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
#        self.assertEquals(response.status_code, 200)
#        self.assertEqual(response.content.count('<li '), 3)
#        # assert copy success
#        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 3)
#        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 3)
#        self.assertEquals(CMSPlugin.objects.count(), 6)
#
#        new_plugin = Text.objects.get(pk=6)
#        self.assertEquals(plugin_tags_to_id_list(new_plugin.body), [u'4', u'5'])
#


#class PluginManyToManyTestCase(PluginsTestBaseCase):
#
#    def setUp(self):
#        self.super_user = User(username="test", is_staff = True, is_active = True, is_superuser = True)
#        self.super_user.set_password("test")
#        self.super_user.save()
#
#        self.slave = User(username="slave", is_staff=True, is_active=True, is_superuser=False)
#        self.slave.set_password("slave")
#        self.slave.save()
#        
#        self._login_context = self.login_user_context(self.super_user)
#        self._login_context.__enter__()
#    
#        # create 3 sections
#        self.sections = []
#        self.section_pks = []
#        for i in range(3):
#            section = Section.objects.create(name="section %s" %i)
#            self.sections.append(section)
#            self.section_pks.append(section.pk)
#        self.section_count = len(self.sections)
#        # create 10 articles by section
#        for section in self.sections:
#            for j in range(10):
#                Article.objects.create(
#                    title="article %s" % j,
#                    section=section
#                )
#        self.FIRST_LANG = settings.LANGUAGES[0][0]
#        self.SECOND_LANG = settings.LANGUAGES[1][0]
#    
#    def test_add_plugin_with_m2m(self):
#        # add a new text plugin
#        page_data = self.get_new_page_data()
#        self.client.post(URL_CMS_PAGE_ADD, page_data)
#        page = Page.objects.all()[0]
#        placeholder = page.placeholders.get(slot="body")
#        plugin_data = {
#            'plugin_type': "ArticlePlugin",
#            'language': self.FIRST_LANG,
#            'placeholder': placeholder.pk,
#        }
#        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
#        self.assertEquals(response.status_code, 200)
#        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
#        # now edit the plugin
#        edit_url = URL_CMS_PLUGIN_EDIT + response.content + "/"
#        response = self.client.get(edit_url)
#        self.assertEquals(response.status_code, 200)
#        data = {
#            'title': "Articles Plugin 1",
#            "sections": self.section_pks
#        }
#        response = self.client.post(edit_url, data)
#        self.assertEqual(response.status_code, 200)
#        self.assertEqual(ArticlePluginModel.objects.count(), 1)
#        plugin = ArticlePluginModel.objects.all()[0]
#        self.assertEquals(self.section_count, plugin.sections.count())
#
#    def test_add_plugin_with_m2m_and_publisher(self):
#        page_data = self.get_new_page_data()
#        self.client.post(URL_CMS_PAGE_ADD, page_data)
#        page = Page.objects.all()[0]
#        placeholder = page.placeholders.get(slot="body")
#
#        # add a plugin
#        plugin_data = {
#            'plugin_type': "ArticlePlugin",
#            'language': self.FIRST_LANG,
#            'placeholder': placeholder.pk,
#
#        }
#        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
#        self.assertEquals(response.status_code, 200)
#        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
#
#        # there should be only 1 plugin
#        self.assertEquals(1, CMSPlugin.objects.all().count())
#
#        articles_plugin_pk = int(response.content)
#        self.assertEquals(articles_plugin_pk, CMSPlugin.objects.all()[0].pk)
#        # now edit the plugin
#        edit_url = URL_CMS_PLUGIN_EDIT + response.content + "/"
#
#        data = {
#            'title': "Articles Plugin 1",
#            'sections': self.section_pks
#        }
#        response = self.client.post(edit_url, data)
#        self.assertEquals(response.status_code, 200)
#        self.assertEquals(1, ArticlePluginModel.objects.count())
#        articles_plugin = ArticlePluginModel.objects.all()[0]
#        self.assertEquals(u'Articles Plugin 1', articles_plugin.title)
#        self.assertEquals(self.section_count, articles_plugin.sections.count())
#
#
#        # check publish box
#        page = publish_page(page, self.super_user)
#
#        # there should now be two plugins - 1 draft, 1 public
#        self.assertEquals(2, ArticlePluginModel.objects.all().count())
#
#        db_counts = [plugin.sections.count() for plugin in ArticlePluginModel.objects.all()]
#        expected = [self.section_count for i in range(len(db_counts))]
#        self.assertEqual(expected, db_counts)
#
#
#    def test_copy_plugin_with_m2m(self):
#        page = create_page("page", "nav_playground.html", "en")
#        
#        placeholder = page.placeholders.get(slot='body')
#
#        plugin = ArticlePluginModel(
#            plugin_type='ArticlePlugin',
#            placeholder=placeholder,
#            position=1,
#            language=self.FIRST_LANG)
#        plugin.insert_at(None, position='last-child', save=True)
#
#        edit_url = URL_CMS_PLUGIN_EDIT + str(plugin.pk) + "/"
#
#        data = {
#            'title': "Articles Plugin 1",
#            "sections": self.section_pks
#        }
#        response = self.client.post(edit_url, data)
#        self.assertEquals(response.status_code, 200)
#        self.assertEqual(ArticlePluginModel.objects.count(), 1)
#
#        self.assertEqual(ArticlePluginModel.objects.all()[0].sections.count(), self.section_count)
#
#        page_data = self.get_new_page_data()
#
#        #create 2nd language page
#        page_data.update({
#            'language': self.SECOND_LANG,
#            'title': "%s %s" % (page.get_title(), self.SECOND_LANG),
#        })
#        response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk + "?language=%s" % self.SECOND_LANG, page_data)
#        self.assertRedirects(response, URL_CMS_PAGE)
#
#        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 1)
#        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 0)
#        self.assertEquals(CMSPlugin.objects.count(), 1)
#        self.assertEquals(Page.objects.all().count(), 1)
#        copy_data = {
#            'placeholder': placeholder.pk,
#            'language': self.SECOND_LANG,
#            'copy_from': self.FIRST_LANG,
#        }
#        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
#        self.assertEquals(response.status_code, 200)
#        self.assertEqual(response.content.count('<li '), 1)
#        # assert copy success
#        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 1)
#        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 1)
#        self.assertEquals(CMSPlugin.objects.count(), 2)
#        db_counts = [plugin.sections.count() for plugin in ArticlePluginModel.objects.all()]
#        expected = [self.section_count for i in range(len(db_counts))]
#        self.assertEqual(expected, db_counts)
        
