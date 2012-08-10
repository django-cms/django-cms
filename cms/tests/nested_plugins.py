# -*- coding: utf-8 -*-
from __future__ import with_statement

from cms.api import create_page, add_plugin
from cms.models import Page
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.tests.plugins import PluginsTestBaseCase
from cms.test_utils.util.context_managers import SettingsOverride


URL_CMS_MOVE_PLUGIN = u'/admin/cms/page/%d/move-plugin/'    


class NestedPluginsTestCase(PluginsTestBaseCase):
    
    def test_nested_plugin_on_page(self):
        """
        Validate a textplugin with a nested link plugin
        mptt values are correctly showing a parent child relationship
        of a nested plugin
        """
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            # setup page 1
            page_one = create_page(u"Three Placeholder", u"col_three.html", u"en",
                               position=u"last-child", published=True, in_navigation=True)
            page_one_ph_two = page_one.placeholders.get(slot=u"col_left")
            
            ###
            # add a plugin
            ###
            pre_nesting_body = u"<p>the nested text plugin with a link inside</p>"
            text_plugin = add_plugin(page_one_ph_two, u"TextPlugin", u"en", body=pre_nesting_body)
            # prepare nestin plugin
            page_one_ph_two = self.reload(page_one_ph_two)
            text_plugin = self.reload(text_plugin)
            link_plugin = add_plugin(page_one_ph_two, u"LinkPlugin", u"en", target=text_plugin)
            link_plugin.name = u"django-cms Link"
            link_plugin.url = u"https://www.django-cms.org" 
            
            # as for some reason mptt does not 
            # update the parent child relationship 
            # in the add_plugin method when a target present
            # but this is not the topic of the test
            link_plugin.parent = text_plugin
            link_plugin.save()
            # reloading needs to be done after every save
            link_plugin = self.reload(link_plugin)
            text_plugin = self.reload(text_plugin)
            
            # mptt related insertion correct?
            msg = u"parent plugin right is not updated, child not inserted correctly"
            self.assertTrue(text_plugin.rght > link_plugin.rght, msg=msg)
            msg = u"link has no parent"
            self.assertFalse(link_plugin.parent == None, msg=msg)
            msg = u"parent plugin left is not updated, child not inserted correctly"
            self.assertTrue(text_plugin.lft < link_plugin.lft, msg=msg)
            msg = u"child level is not bigger than parent level"
            self.assertTrue(text_plugin.level < link_plugin.level , msg=msg)
            
            # add the link plugin to the body
            # emulate the editor in admin that adds some txt for the nested plugin
            in_txt = u"""<img id="plugin_obj_%s" title="Link" alt="Link" src="/static/cms/images/plugins/link.png">"""
            nesting_body = u"%s<p>%s</p>" % (text_plugin.body, (in_txt % (link_plugin.id)))
            text_plugin.body = nesting_body
            text_plugin.save()
            
            text_plugin = self.reload(text_plugin)
            # none of the descendants should have a placeholder other then my own one
            self.assertEquals(text_plugin.get_descendants().exclude(placeholder=text_plugin.placeholder).count(), 0)
            post_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(post_add_plugin_count, 2)
            
    
    
    def test_copy_page_nested_plugin(self):
        """
        Test to verify that page copy with a nested plugin works
        page one - 3 placeholder 
                    col_sidebar: 
                        1 text plugin
                    col_left: 1 text plugin with nested link plugin
                    col_right: no plugin
        page two (copy target)
        Verify copied page, placeholders, plugins and body text
        """
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            templates = []
            # setup page 1
            page_one = create_page(u"Three Placeholder", u"col_three.html", u"en",
                               position=u"last-child", published=True, in_navigation=True)
            page_one_ph_one = page_one.placeholders.get(slot=u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot=u"col_left")
            page_one_ph_three = page_one.placeholders.get(slot=u"col_right")
            # add the text plugin to placeholder one
            text_plugin_en = add_plugin(page_one_ph_one, u"TextPlugin", u"en", body="Hello World")
            self.assertEquals(text_plugin_en.id, CMSPlugin.objects.all()[0].id)
            self.assertEquals(text_plugin_en.get_children().count(), 0)
            pre_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(pre_add_plugin_count, 1)
            ###
            # add a plugin to placeholder two
            ###
            pre_nesting_body = u"<p>the nested text plugin with a link inside</p>"
            text_plugin_two = add_plugin(page_one_ph_two, u"TextPlugin", u"en", body=pre_nesting_body)
            text_plugin_two = self.reload(text_plugin_two)
            # prepare nesting plugin
            page_one_ph_two = self.reload(page_one_ph_two)
            text_plugin_two = self.reload(text_plugin_two)
            link_plugin = add_plugin(page_one_ph_two, u"LinkPlugin", u"en", target=text_plugin_two)
            link_plugin.name = u"django-cms Link"
            link_plugin.url = u"https://www.django-cms.org" 
            link_plugin.parent = text_plugin_two
            link_plugin.save()
            
            link_plugin = self.reload(link_plugin)
            text_plugin_two = self.reload(text_plugin_two)
            in_txt = """<img id="plugin_obj_%s" title="Link" alt="Link" src="/static/cms/images/plugins/link.png">"""
            nesting_body = "%s<p>%s</p>" % (text_plugin_two.body, (in_txt % (link_plugin.id)))
            # emulate the editor in admin that adds some txt for the nested plugin
            text_plugin_two.body = nesting_body
            text_plugin_two.save()
            text_plugin_two = self.reload(text_plugin_two)
            # the link is attached as a child?
            self.assertEquals(text_plugin_two.get_children().count(), 1)
            post_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(post_add_plugin_count, 3)
            page_one.save()
            # get the plugins from the original page
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.placeholders.get(slot = u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot = u"col_left")
            page_one_ph_three = page_one.placeholders.get(slot = u"col_right")
            # verifiy the plugins got created
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
            # setup page_copy_target page
            ##
            page_copy_target = create_page("Three Placeholder - page copy target", "col_three.html", "en",
                               position="last-child", published=True, in_navigation=True)
            all_page_count = Page.objects.all().count()
            pre_copy_placeholder_count = Placeholder.objects.count()
            self.assertEquals(pre_copy_placeholder_count, 6)
            # copy the page
            superuser = self.get_superuser()
            with self.login_user_context(superuser):
                page_two = self.copy_page(page_one, page_copy_target)
            # validate the expected pages,placeholders,plugins,pluginbodies
            after_copy_page_plugin_count = CMSPlugin.objects.count()
            self.assertEquals(after_copy_page_plugin_count, 6)
            # check the amount of copied stuff
            after_copy_page_count = Page.objects.all().count()
            after_copy_placeholder_count = Placeholder.objects.count()
            self.assertTrue((after_copy_page_count > all_page_count), msg = u"no new page after copy")
            self.assertTrue((after_copy_page_plugin_count > post_add_plugin_count), msg = u"plugin count is not grown")
            self.assertTrue((after_copy_placeholder_count > pre_copy_placeholder_count), msg = u"placeholder count is not grown")    
            self.assertTrue((after_copy_page_count == 3), msg = u"no new page after copy")
            # orginal placeholder
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.placeholders.get(slot = u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot = u"col_left")
            page_one_ph_three = page_one.placeholders.get(slot = u"col_right")
            # check if there are multiple pages assigned to this placeholders
            found_page = page_one_ph_one.page if page_one_ph_one else None
            self.assertEqual(found_page, page_one)
            found_page = page_one_ph_two.page if page_one_ph_two else None
            self.assertEqual(found_page, page_one)
            found_page = page_one_ph_three.page if page_one_ph_three else None
            self.assertEqual(found_page, page_one)
            
            page_two = self.reload(page_two)
            page_two_ph_one = page_two.placeholders.get(slot = u"col_sidebar")
            page_two_ph_two = page_two.placeholders.get(slot = u"col_left")
            page_two_ph_three = page_two.placeholders.get(slot = u"col_right")
            # check if there are multiple pages assigned to this placeholders
            found_page = page_two_ph_one.page if page_two_ph_one else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_two.page if page_two_ph_two else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_three.page if page_two_ph_three else None
            self.assertEqual(found_page, page_two)
            # check the stored placeholders org vs copy
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (page_two_ph_one.pk, page_one_ph_one.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_one.pk, page_one_ph_one.pk, msg)
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (page_two_ph_two.pk, page_one_ph_two.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_two.pk, page_one_ph_two.pk, msg)
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (page_two_ph_three.pk, page_one_ph_three.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_three.pk, page_one_ph_three.pk, msg)
            # get the plugins from the original page
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEquals(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEquals(len(org_placeholder_two_plugins), 2)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEquals(len(org_placeholder_three_plugins), 0)
            # get the plugins from the copied page
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
            msg = u"plugin count %s %s for placeholder one not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEquals(count_plugins_copied, count_plugins_org, msg)        
            # placeholder 2
            count_plugins_copied = len(copied_placeholder_two_plugins)
            count_plugins_org = len(org_placeholder_two_plugins)
            msg = u"plugin count %s %s for placeholder two not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEquals(count_plugins_copied, count_plugins_org, msg)        
            # placeholder 3
            count_plugins_copied = len(copied_placeholder_three_plugins)
            count_plugins_org = len(org_placeholder_three_plugins)
            msg = u"plugin count %s %s for placeholder three not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEquals(count_plugins_copied, count_plugins_org, msg)
            # verify the body of text plugin with nested link plugin
            # org to copied  
            org_nested_text_plugin = None
            # do this iteration to find the real text plugin with the attached link
            # the inheritance mechanism for the cmsplugins works through 
            # (tuple)get_plugin_instance()
            for x in org_placeholder_two_plugins:     
                if x.plugin_type == u"TextPlugin":
                    instance = x.get_plugin_instance()[0]
                    if instance.body.startswith(pre_nesting_body):
                        org_nested_text_plugin = instance
                        break
            copied_nested_text_plugin = None
            for x in copied_placeholder_two_plugins:        
                if x.plugin_type == u"TextPlugin":
                    instance = x.get_plugin_instance()[0]
                    if instance.body.startswith(pre_nesting_body):
                        copied_nested_text_plugin = instance
                        break
            msg = u"orginal nested text plugin not found"
            self.assertNotEquals(org_nested_text_plugin, None, msg=msg)
            msg = u"copied nested text plugin not found"
            self.assertNotEquals(copied_nested_text_plugin, None, msg=msg)
            # get the children ids of the texplugin with a nested link
            # to check if the body of the text is genrated correctly
            org_link_child_plugin = org_nested_text_plugin.get_children()[0]
            copied_link_child_plugin = copied_nested_text_plugin.get_children()[0]
            # validate the textplugin body texts
            msg = u"org plugin and copied plugin are the same"
            self.assertTrue(org_link_child_plugin.id != copied_link_child_plugin.id, msg)
            needle = u"plugin_obj_%s"
            msg = u"child plugin id differs to parent in body plugin_obj_id"
            # linked child is in body
            self.assertTrue(org_nested_text_plugin.body.find(needle % (org_link_child_plugin.id)) != -1, msg)
            msg = u"copy: child plugin id differs to parent in body plugin_obj_id"
            self.assertTrue(copied_nested_text_plugin.body.find(needle % (copied_link_child_plugin.id)) != -1, msg)
            # really nothing else
            msg = u"child link plugin id differs to parent body plugin_obj_id"
            self.assertTrue(org_nested_text_plugin.body.find(needle % (copied_link_child_plugin.id)) == -1, msg)
            msg = u"copy: child link plugin id differs to parent body plugin_obj_id"
            self.assertTrue(copied_nested_text_plugin.body.find(needle % (org_link_child_plugin.id)) == -1, msg)
            # now reverse lookup the placeholders from the plugins
            org_placeholder = org_link_child_plugin.placeholder
            copied_placeholder = copied_link_child_plugin.placeholder
            msg = u"placeholder of the orginal plugin and copied plugin are the same"
            ok = ((org_placeholder.id != copied_placeholder.id))
            self.assertTrue(ok, msg)

     
    def test_copy_page_nested_plugin_moved_parent_plugin(self):
        """
        Test to verify that page copy with a nested plugin works
        when a plugin with child got moved to another placeholder
        page one - 3 placeholder 
                    col_sidebar: 
                        1 text plugin
                    col_left: 1 text plugin with nested link plugin
                    col_right: no plugin
        page two (copy target)
        step2: move the col_left text plugin to col_right
                    col_sidebar: 
                        1 text plugin
                    col_left: no plugin
                    col_right: 1 text plugin with nested link plugin
        verify the copied page structure
        """
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            templates = []
            # setup page 1
            page_one = create_page(u"Three Placeholder", u"col_three.html", u"en",
                               position=u"last-child", published=True, in_navigation=True)
            page_one_ph_one = page_one.placeholders.get(slot=u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot=u"col_left")
            page_one_ph_three = page_one.placeholders.get(slot=u"col_right")
            # add the text plugin to placeholder one
            text_plugin_en = add_plugin(page_one_ph_one, u"TextPlugin", u"en", body=u"Hello World")
            self.assertEquals(text_plugin_en.id, CMSPlugin.objects.all()[0].id)
            self.assertEquals(text_plugin_en.get_children().count(), 0)
            pre_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(pre_add_plugin_count, 1)
            # add a plugin to placeholder twho
            pre_nesting_body = u"<p>the nested text plugin with a link inside</p>"
            text_plugin_two = add_plugin(page_one_ph_two, u"TextPlugin", u"en", body=pre_nesting_body)
            text_plugin_two = self.reload(text_plugin_two)
            # prepare nestin plugin
            page_one_ph_two = self.reload(page_one_ph_two)
            text_plugin_two = self.reload(text_plugin_two)
            link_plugin = add_plugin(page_one_ph_two, u"LinkPlugin", u"en", target=text_plugin_two)
            link_plugin.name = u"django-cms Link"
            link_plugin.url = u"https://www.django-cms.org" 
            link_plugin.parent = text_plugin_two
            link_plugin.save()
            # reload after every save
            link_plugin = self.reload(link_plugin)
            text_plugin_two = self.reload(text_plugin_two)
            in_txt = u"""<img id="plugin_obj_%s" title="Link" alt="Link" src="/static/cms/images/plugins/link.png">"""
            nesting_body = "%s<p>%s</p>" % (text_plugin_two.body, (in_txt % (link_plugin.id)))
            # emulate the editor in admin that adds some txt for the nested plugin
            text_plugin_two.body = nesting_body
            text_plugin_two.save()
            text_plugin_two = self.reload(text_plugin_two)
            # the link is attached as a child?
            self.assertEquals(text_plugin_two.get_children().count(), 1)
            post_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(post_add_plugin_count, 3)
            page_one.save()
            # get the plugins from the original page
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.placeholders.get(slot = u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot = u"col_left")
            page_one_ph_three = page_one.placeholders.get(slot = u"col_right")
            # verify the plugins got created
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
            # setup page_copy_target
            page_copy_target = create_page("Three Placeholder - page copy target", "col_three.html", "en",
                               position="last-child", published=True, in_navigation=True)
            all_page_count = Page.objects.all().count()
            pre_copy_placeholder_count = Placeholder.objects.count()
            self.assertEquals(pre_copy_placeholder_count, 6)
            superuser = self.get_superuser()
            with self.login_user_context(superuser):
                # now move the parent text plugin to another placeholder
                post_data = {
                             u'placeholder': u"col_right",
                             u'placeholder_id': u"%s" % (page_one_ph_three.id),
                             u'ids': u"%s" % (text_plugin_two.id),
                             u'plugin_id': u"%s" % (text_plugin_two.id),
                }
                edit_url = URL_CMS_MOVE_PLUGIN % (page_one.id)
                response = self.client.post(edit_url, post_data)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, u'ok')
                # check if the plugin got moved
                page_one = self.reload(page_one)
                text_plugin_two = self.reload(text_plugin_two)
                page_one_ph_one = page_one.placeholders.get(slot = u"col_sidebar")
                page_one_ph_two = page_one.placeholders.get(slot = u"col_left")
                page_one_ph_three = page_one.placeholders.get(slot = u"col_right")
                
                org_placeholder_one_plugins = page_one_ph_one.get_plugins()
                self.assertEquals(len(org_placeholder_one_plugins), 1)
                org_placeholder_two_plugins = page_one_ph_two.get_plugins()
                # the plugin got moved and child got moved
                self.assertEquals(len(org_placeholder_two_plugins), 0)
                org_placeholder_three_plugins = page_one_ph_three.get_plugins()
                self.assertEquals(len(org_placeholder_three_plugins), 2)
                # copy the page
                page_two = self.copy_page(page_one, page_copy_target)
            # validate the expected pages,placeholders,plugins,pluginbodies
            after_copy_page_plugin_count = CMSPlugin.objects.count()
            self.assertEquals(after_copy_page_plugin_count, 6)
            after_copy_page_count = Page.objects.all().count()
            after_copy_placeholder_count = Placeholder.objects.count()
            self.assertTrue((after_copy_page_count > all_page_count), msg = u"no new page after copy")
            self.assertTrue((after_copy_page_plugin_count > post_add_plugin_count), msg = u"plugin count is not grown")
            self.assertTrue((after_copy_placeholder_count > pre_copy_placeholder_count), msg = u"placeholder count is not grown")    
            self.assertTrue((after_copy_page_count == 3), msg = u"no new page after copy")
            # validate the structure
            # orginal placeholder
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.placeholders.get(slot=u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot=u"col_left")
            page_one_ph_three = page_one.placeholders.get(slot=u"col_right")
            # check if there are multiple pages assigned to this placeholders
            found_page = page_one_ph_one.page if page_one_ph_one else None
            self.assertEqual(found_page, page_one)
            found_page = page_one_ph_two.page if page_one_ph_two else None
            self.assertEqual(found_page, page_one)
            found_page = page_one_ph_three.page if page_one_ph_three else None
            self.assertEqual(found_page, page_one)
            page_two = self.reload(page_two)
            page_two_ph_one = page_two.placeholders.get(slot = u"col_sidebar")
            page_two_ph_two = page_two.placeholders.get(slot = u"col_left")
            page_two_ph_three = page_two.placeholders.get(slot = u"col_right")
            # check if there are multiple pages assigned to this placeholders
            found_page = page_two_ph_one.page if page_two_ph_one else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_two.page if page_two_ph_two else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_three.page if page_two_ph_three else None
            self.assertEqual(found_page, page_two)
            # check the stored placeholders org vs copy
            msg = u'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (page_two_ph_one.pk, page_one_ph_one.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_one.pk, page_one_ph_one.pk, msg)
            msg = u'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (page_two_ph_two.pk, page_one_ph_two.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_two.pk, page_one_ph_two.pk, msg)
            msg = u'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (page_two_ph_three.pk, page_one_ph_three.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_three.pk, page_one_ph_three.pk, msg)
            # get the plugins from the original page
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEquals(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEquals(len(org_placeholder_two_plugins), 0)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEquals(len(org_placeholder_three_plugins), 2)
            # get the plugins from the copied page
            copied_placeholder_one_plugins = page_two_ph_one.get_plugins()
            self.assertEquals(len(copied_placeholder_one_plugins), 1)
            copied_placeholder_two_plugins = page_two_ph_two.get_plugins()
            self.assertEquals(len(copied_placeholder_two_plugins), 0)
            copied_placeholder_three_plugins = page_two_ph_three.get_plugins()
            self.assertEquals(len(copied_placeholder_three_plugins), 2)
            # verify the plugins got copied
            # placeholder 1
            count_plugins_copied = len(copied_placeholder_one_plugins)
            count_plugins_org = len(org_placeholder_one_plugins)
            msg = u"plugin count %s %s for placeholder one not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEquals(count_plugins_copied, count_plugins_org, msg)        
            # placeholder 2
            count_plugins_copied = len(copied_placeholder_two_plugins)
            count_plugins_org = len(org_placeholder_two_plugins)
            msg = u"plugin count %s %s for placeholder two not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEquals(count_plugins_copied, count_plugins_org, msg)        
            # placeholder 3
            count_plugins_copied = len(copied_placeholder_three_plugins)
            count_plugins_org = len(org_placeholder_three_plugins)
            msg = u"plugin count %s %s for placeholder three not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEquals(count_plugins_copied, count_plugins_org, msg)
            # verify the body of text plugin with nested link plugin
            # org to copied  
            org_nested_text_plugin = None
            # do this iteration to find the real text plugin with the attached link
            # the inheritance mechanism for the cmsplugins works through 
            # (tuple)get_plugin_instance()
            for x in org_placeholder_three_plugins:     
                if x.plugin_type == u"TextPlugin":
                    instance = x.get_plugin_instance()[0]
                    if instance.body.startswith(pre_nesting_body):
                        org_nested_text_plugin = instance
                        break
            copied_nested_text_plugin = None
            for x in copied_placeholder_three_plugins:        
                if x.plugin_type == u"TextPlugin":
                    instance = x.get_plugin_instance()[0]
                    if instance.body.startswith(pre_nesting_body):
                        copied_nested_text_plugin = instance
                        break
            msg = u"orginal nested text plugin not found"
            self.assertNotEquals(org_nested_text_plugin, None, msg=msg)
            msg = u"copied nested text plugin not found"
            self.assertNotEquals(copied_nested_text_plugin, None, msg=msg)
            # get the children ids of the texplugin with a nested link
            # to check if the body of the text is generated correctly
            org_link_child_plugin = org_nested_text_plugin.get_children()[0]
            copied_link_child_plugin = copied_nested_text_plugin.get_children()[0]
            # validate the textplugin body texts
            msg = u"org plugin and copied plugin are the same"
            self.assertTrue(org_link_child_plugin.id != copied_link_child_plugin.id, msg)
            needle = u"plugin_obj_%s"
            msg = u"child plugin id differs to parent in body plugin_obj_id"
            # linked child is in body
            self.assertTrue(org_nested_text_plugin.body.find(needle % (org_link_child_plugin.id)) != -1, msg)
            msg = u"copy: child plugin id differs to parent in body plugin_obj_id"
            self.assertTrue(copied_nested_text_plugin.body.find(needle % (copied_link_child_plugin.id)) != -1, msg)
            # really nothing else
            msg = u"child link plugin id differs to parent body plugin_obj_id"
            self.assertTrue(org_nested_text_plugin.body.find(needle % (copied_link_child_plugin.id)) == -1, msg)
            msg = u"copy: child link plugin id differs to parent body plugin_obj_id"
            self.assertTrue(copied_nested_text_plugin.body.find(needle % (org_link_child_plugin.id)) == -1, msg)
            # now reverse lookup the placeholders from the plugins
            org_placeholder = org_link_child_plugin.placeholder
            copied_placeholder = copied_link_child_plugin.placeholder
            msg = u"placeholder of the orginal plugin and copied plugin are the same"
            ok = ((org_placeholder.id != copied_placeholder.id))
            self.assertTrue(ok, msg)       
