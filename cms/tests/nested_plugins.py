# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page,add_plugin
from cms.models import Page
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.tests.plugins import PluginsTestBaseCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils.placeholder import get_page_from_placeholder_if_exists
    

class PluginsTestCase(PluginsTestBaseCase):
    
    def test_copy_page_nested_plugin(self):
        """
        Test to verify that a page with a simple nested plugin works
        page one - 3 placeholder 
                    col_sidebar: 
                        1 text plugin
                    col_left: 1 text plugin with nested link plugin
                    col_right: no plugin
        page two (copy target)
        """
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            templates = []
            # setup page 1
            page_one = create_page("Three Placeholder", "col_three.html", "en",
                               position="last-child", published=True, in_navigation=True)
            page_one_ph_one = page_one.placeholders.get(slot="col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot="col_left")
            page_one_ph_three = page_one.placeholders.get(slot="col_right")
            
            # add the text plugin to placeholder one
            text_plugin_en = add_plugin(page_one_ph_one, "TextPlugin", "en", body="Hello World")
            self.assertEquals(text_plugin_en.pk, CMSPlugin.objects.all()[0].pk)
            self.assertEquals(text_plugin_en.get_children().count(), 0)
            pre_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(pre_add_plugin_count, 1)
            ###
            # add a plugin
            ###
            text_plugin_two = add_plugin(page_one_ph_two, "TextPlugin", "en", body="<p>the nested text plugin with a link inside</p>")
            # prepare nestin plugin
            link_plugin = CMSPlugin(language="en",
                                    plugin_type="LinkPlugin",
                                    position=None,
                                    placeholder=page_one_ph_two)
            link_plugin.parent = text_plugin_two
            link_plugin.save()
            link_plugin.name = "django-cms Link"
            link_plugin.url = "https://www.django-cms.org" 
            link_plugin.save()
            text_plugin_two.save()
            ###
            # add the link plugin to inline txt plugin
            link_plugin = self.reload(link_plugin)
            text_plugin_two = self.reload(text_plugin_two)
            in_txt = """<img id="plugin_obj_%s" title="Link" alt="Link" src="/static/cms/images/plugins/link.png">"""
            new_txt = "%s<p>%s</p>" % (text_plugin_two.body, (in_txt % (link_plugin.id)))
            text_plugin_two.body = new_txt
            text_plugin_two.save()
            self.assertEquals(text_plugin_two.get_children().count(), 0)
            post_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(post_add_plugin_count, 3)
            page_one.save()
            ###
            # get the plugins from the original page
            ###
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.placeholders.get(slot="col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot="col_left")
            page_one_ph_three = page_one.placeholders.get(slot="col_right")
            ###
            # verifiy the plugins got created
            ###
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEquals(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEquals(len(org_placeholder_two_plugins), 2)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEquals(len(org_placeholder_three_plugins), 0)
            self.assertEquals(page_one.placeholders.count(), 3)
            placeholder_count = Placeholder.objects.count()
            self.assertEquals(placeholder_count, 3)
            self.assertEquals(CMSPlugin.objects.count(), 3)
            page_one_plugins = CMSPlugin.objects.all()
            
            ##
            # setup page 2 - copy target
            ##
            page_two = create_page("Three Placeholder - page 2", "col_three.html", "en",
                               position="last-child", published=True, in_navigation=True)
            all_page_count = Page.objects.all().count()
            pre_copy_placeholder_count = Placeholder.objects.count()
            self.assertEquals(pre_copy_placeholder_count, 6)
            ##
            # copy the page
            ##
            superuser = self.get_superuser()
            with self.login_user_context(superuser):
                page_two = self.copy_page(page_one, page_two)
                
            after_copy_page_plugin_count = CMSPlugin.objects.count()
            self.assertEquals(after_copy_page_plugin_count, 6)
            
            after_copy_page_count = Page.objects.all().count()
            after_copy_placeholder_count = Placeholder.objects.count()
            
            self.assertTrue((after_copy_page_count > all_page_count), msg="no new page after copy")
            self.assertTrue((after_copy_page_plugin_count > post_add_plugin_count), msg="plugin count is not grown")
            self.assertTrue((after_copy_placeholder_count > pre_copy_placeholder_count), msg="placeholder count is not grown")    
            ###
            # orginal placeholder
            ###
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.placeholders.get(slot="col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot="col_left")
            page_one_ph_three = page_one.placeholders.get(slot="col_right")
            ##
            # check if there are multiple pages assigned to this placeholders
            found_page = get_page_from_placeholder_if_exists(page_one_ph_one)
            self.assertEqual(found_page, page_one)
            found_page = get_page_from_placeholder_if_exists(page_one_ph_two)
            self.assertEqual(found_page, page_one)
            found_page = get_page_from_placeholder_if_exists(page_one_ph_three)
            self.assertEqual(found_page, page_one)
            
            page_two = self.reload(page_two)
            page_two_ph_one = page_two.placeholders.get(slot="col_sidebar")
            page_two_ph_two = page_two.placeholders.get(slot="col_left")
            page_two_ph_three = page_two.placeholders.get(slot="col_right")
    
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (page_two_ph_one.pk, page_one_ph_one.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_one.pk, page_one_ph_one.pk, msg)
            
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (page_two_ph_two.pk, page_one_ph_two.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_two.pk, page_one_ph_two.pk, msg)
            
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (page_two_ph_three.pk, page_one_ph_three.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_three.pk, page_one_ph_three.pk, msg)
            ###
            # check all plugins to which placeholder they relate
            ###
#            at_page_one = []
#            at_page_two = []
#            at_undefined = []
#            print "page one id %s" % (page_one.pk)
#            print "page two id %s" % (page_two.pk)
#            all_plugins = CMSPlugin.objects.all()
#            for plugin in all_plugins:
#                if plugin.placeholder in [page_one_ph_one,
#                                          page_one_ph_two,
#                                          page_one_ph_three,
#                                          ]:
#                    at_page_one.append(plugin)
#                    print "one placeholder %s ph_id:%s page_set:%s page_0_id %s" % (plugin.placeholder, plugin.placeholder.pk, plugin.placeholder.page_set.all(), plugin.placeholder.page_set.all()[0].id)
#                elif plugin.placeholder in [page_two_ph_one,
#                                            page_two_ph_two,
#                                            page_two_ph_three,
#                                            ]:
#                    at_page_two.append(plugin)
#                else:
#                    at_undefined.append(plugin)
#                    print "undefined placeholder %s ph_id:%s page_set:%s page_0_id %s" % (plugin.placeholder, plugin.placeholder.pk, plugin.placeholder.page_set.all(), plugin.placeholder.page_set.all()[0].id)
#                    
#            print "at one %s" % at_page_one
#            print "at two %s" % at_page_two
#            print "at undefined %s" % at_undefined
#            
#           
            ###
            # get the plugins from the original page
            ###
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEquals(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEquals(len(org_placeholder_two_plugins), 2)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEquals(len(org_placeholder_three_plugins), 0)
            ###
            # get the plugins from the copied page
            ###
            copied_placeholder_one_plugins = page_two_ph_one.get_plugins()
            self.assertEquals(len(copied_placeholder_one_plugins), 1)
            copied_placeholder_two_plugins = page_two_ph_two.get_plugins()
            self.assertEquals(len(copied_placeholder_two_plugins), 2)
            copied_placeholder_three_plugins = page_two_ph_three.get_plugins()
            self.assertEquals(len(copied_placeholder_three_plugins), 0)
            
            # verify the plugins got copied
            # placeholder 1
            count_plugins_copied = len(copied_placeholder_one_plugins)
            count_plugins_org = len(org_placeholder_one_plugins)
            msg = "plugin count %s %s for placeholder one not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEquals(count_plugins_copied, count_plugins_org, msg)        
            # placeholder 2
            count_plugins_copied = len(copied_placeholder_two_plugins)
            count_plugins_org = len(org_placeholder_two_plugins)
            msg = "plugin count %s %s for placeholder two not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEquals(count_plugins_copied, count_plugins_org, msg)        
            # placeholder 3
            count_plugins_copied = len(copied_placeholder_three_plugins)
            count_plugins_org = len(org_placeholder_three_plugins)
            msg = "plugin count %s %s for placeholder three not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEquals(count_plugins_copied, count_plugins_org, msg)        
        
