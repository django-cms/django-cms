from djangocms_text_ckeditor.models import Text

from cms.api import add_plugin, create_page
from cms.models import Page
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.tests.test_plugins import PluginsTestBaseCase
from cms.utils.plugins import copy_plugins_to_placeholder


class NestedPluginsTestCase(PluginsTestBaseCase):

    def compare_plugin_tree(self, tree, placeholder):
        counter = 1
        plugins = placeholder.get_plugins()

        for plugin, data in zip(plugins, tree):
            msg = 'Expected %s %s. Got %s instead.'
            self.assertEqual(plugin.pk, data[0], msg % ('id', data[0], plugin.pk))
            self.assertEqual(plugin.position, counter, msg % ('position', counter, plugin.position))
            self.assertEqual(plugin.parent_id, data[1], msg % ('parent', data[1], plugin.parent_id))
            counter += 1

    def copy_placeholders_and_check_results(self, placeholders):
        """
        This function is not itself a test; rather, it can be used by any test
        that has created placeholders. It will check that whatever the plugin
        structure in the placeholder, it will be copied accurately when they are
        copied.

        placeholders is a list of placeholders
        """
        for original_placeholder in placeholders:

            # get the plugins
            original_plugins = original_placeholder.get_plugins()

            # copy them to a new placeholder
            copied_placeholder = Placeholder.objects.create(slot=original_placeholder.slot)
            copy_plugins_to_placeholder(
                original_placeholder.get_plugins(),
                placeholder=copied_placeholder,
            )

            copied_plugins = copied_placeholder.get_plugins()

            # we should find the same number of plugins in both placeholders
            self.assertEqual(
                original_plugins.count(),
                copied_plugins.count()
            )

            # quick check: make sure the two querysets match:
            for original, copy in zip(original_plugins, copied_plugins):
                self.assertEqual(
                    Text.objects.get(id=original.id).body,
                    Text.objects.get(id=copy.id).body
                )
                self.assertEqual(original.position, copy.position)
                self.assertEqual(
                    original._get_descendants_count(),
                    copy._get_descendants_count()
                )
        # just in case the test method that called us wants it:
        return copied_placeholder

    def test_plugin_deep_nesting_and_copying(self):
        """
        Create a deeply-nested plugin structure, tests its properties, and tests
        that it is copied accurately when the placeholder containing them is
        copied.

        The structure below isn't arbitrary, but has been designed to test
        various conditions, including:

        * nodes four levels deep
        * multiple successive level increases
        * multiple successive level decreases
        * successive nodes on the same level followed by level changes
        * multiple level decreases between successive nodes
        * siblings with and without children
        * nodes and branches added to the tree out of sequence

        First we create the structure:

             11
             1
                 2
                     12
                     4
                          10
                     8
                 3
                     9
             5
                 6
                 7
                 13
             14

        and then we move it all around.
        """
        placeholder = Placeholder(slot="some_slot")
        placeholder.save()  # a good idea, if not strictly necessary

        # plugin in placeholder
        plugin_1 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="01"
        )

        # child of plugin_1
        plugin_2 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="02",
            target=plugin_1,
        )
        # plugin_2 should be plugin_1's only child
        # for a single item we use assertSequenceEqual
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_1.pk).get_children(),
            [CMSPlugin.objects.get(id=plugin_2.pk)]
        )

        # create a second child of plugin_1
        plugin_3 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="03",
            target=plugin_1
        )
        # plugin_2 & plugin_3 should be plugin_1's children
        # for multiple items we use assertSequenceEqual, because
        # assertSequenceEqual may re-order the list without warning
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_1.pk).get_children(),
            [
                CMSPlugin.objects.get(id=plugin_2.pk),
                CMSPlugin.objects.get(id=plugin_3.pk),
            ])

        # child of plugin_2
        plugin_4 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="04",
            target=plugin_2
        )

        # plugin_4 should be plugin_2's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_2.pk).get_children(),
            [CMSPlugin.objects.get(id=plugin_4.pk)])

        # 2,3 & 4 should be descendants of 1
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_1.pk).get_descendants(),
            [
                # note path ordering of MP reflected here:
                CMSPlugin.objects.get(id=plugin_2.pk),
                CMSPlugin.objects.get(id=plugin_4.pk),
                CMSPlugin.objects.get(id=plugin_3.pk),
            ],
        )
        # create a second root plugin
        plugin_5 = add_plugin(placeholder, "TextPlugin", "en", body="05")

        # child of plugin_5
        plugin_6 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="06",
            target=plugin_5
        )

        # plugin_6 should be plugin_5's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_5.pk).get_children(),
            [CMSPlugin.objects.get(id=plugin_6.pk)])

        # child of plugin_5
        plugin_7 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="07",
            target=plugin_5
        )

        # plugin_7 should be plugin_5's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_5.pk).get_children(),
            [
                CMSPlugin.objects.get(id=plugin_6.pk),
                CMSPlugin.objects.get(id=plugin_7.pk)
            ])

        # 6 & 7 should be descendants of 5
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_5.pk).get_descendants(),
            [
                CMSPlugin.objects.get(id=plugin_6.pk),
                CMSPlugin.objects.get(id=plugin_7.pk),
            ])

        # another child of plugin_2
        plugin_2 = self.reload(plugin_2)
        plugin_8 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="08",
            target=plugin_2
        )

        # plugin_4 should be plugin_2's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_2.pk).get_children(),
            [
                CMSPlugin.objects.get(id=plugin_4.pk),
                CMSPlugin.objects.get(id=plugin_8.pk),
            ])

        # child of plugin_3
        plugin_9 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="09",
            target=self.reload(plugin_3),
        )

        # plugin_9 should be plugin_3's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_3.pk).get_children(),
            [CMSPlugin.objects.get(id=plugin_9.pk)])

        # child of plugin_4
        plugin_10 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="10",
            target=self.reload(plugin_4)
        )

        # plugin_10 should be plugin_4's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_4.pk).get_children(),
            [CMSPlugin.objects.get(id=plugin_10.pk)])

        original_plugins = placeholder.get_plugins()
        self.assertEqual(original_plugins.count(), 10)

        # elder sibling of plugin_1
        plugin_11 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="11",
            target=plugin_1,
            position="left"
        )

        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_1.pk).get_children(),
            [
                CMSPlugin.objects.get(id=plugin_2.pk),
                CMSPlugin.objects.get(id=plugin_3.pk)
            ])

        # elder sibling of plugin_4
        plugin_12 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="12",
            target=self.reload(plugin_4),
            position="left"
        )
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_2.pk).get_children(),
            [
                CMSPlugin.objects.get(id=plugin_12.pk),
                CMSPlugin.objects.get(id=plugin_4.pk),
                CMSPlugin.objects.get(id=plugin_8.pk)
            ])

        # younger sibling of plugin_7
        plugin_13 = add_plugin(
            placeholder, "TextPlugin", "en",
            body="13",
            target=self.reload(plugin_7),
            position="right"
        )

        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_5.pk).get_children(),
            [
                CMSPlugin.objects.get(id=plugin_6.pk),
                CMSPlugin.objects.get(id=plugin_7.pk),
                CMSPlugin.objects.get(id=plugin_13.pk)
            ])

        # new sibling of plugin_5
        plugin_14 = add_plugin(
            placeholder, "TextPlugin", "en", body="14"
        )

        self.assertSequenceEqual(
            CMSPlugin.objects.filter(parent__isnull=True),
            [
                CMSPlugin.objects.get(id=plugin_11.pk),
                CMSPlugin.objects.get(id=plugin_1.pk),
                CMSPlugin.objects.get(id=plugin_5.pk),
                CMSPlugin.objects.get(id=plugin_14.pk)
            ])

        tree = [
            (plugin_11.pk, None),
            (plugin_1.pk, None),
            (plugin_2.pk, plugin_1.pk),
            (plugin_12.pk, plugin_2.pk),
            (plugin_4.pk, plugin_2.pk),
            (plugin_10.pk, plugin_4.pk),
            (plugin_8.pk, plugin_2.pk),
            (plugin_3.pk, plugin_1.pk),
            (plugin_9.pk, plugin_3.pk),
            (plugin_5.pk, None),
            (plugin_6.pk, plugin_5.pk),
            (plugin_7.pk, plugin_5.pk),
            (plugin_13.pk, plugin_5.pk),
            (plugin_14.pk, None),
        ]
        self.copy_placeholders_and_check_results([placeholder])
        self.compare_plugin_tree(tree, placeholder)

        # now let's move plugins around in the tree

        # move plugin_2 before plugin_11
        tree = [
            (plugin_2.pk, None),
            (plugin_12.pk, plugin_2.pk),
            (plugin_4.pk, plugin_2.pk),
            (plugin_10.pk, plugin_4.pk),
            (plugin_8.pk, plugin_2.pk),
            (plugin_11.pk, None),
            (plugin_1.pk, None),
            (plugin_3.pk, plugin_1.pk),
            (plugin_9.pk, plugin_3.pk),
            (plugin_5.pk, None),
            (plugin_6.pk, plugin_5.pk),
            (plugin_7.pk, plugin_5.pk),
            (plugin_13.pk, plugin_5.pk),
            (plugin_14.pk, None),
        ]
        placeholder.move_plugin(plugin=self.reload(plugin_2), target_position=1)
        self.compare_plugin_tree(tree, placeholder)
        self.copy_placeholders_and_check_results([placeholder])

        # move plugin_6 after plugin_7
        tree = [
            (plugin_2.pk, None),
            (plugin_12.pk, plugin_2.pk),
            (plugin_4.pk, plugin_2.pk),
            (plugin_10.pk, plugin_4.pk),
            (plugin_8.pk, plugin_2.pk),
            (plugin_11.pk, None),
            (plugin_1.pk, None),
            (plugin_3.pk, plugin_1.pk),
            (plugin_9.pk, plugin_3.pk),
            (plugin_5.pk, None),
            (plugin_7.pk, plugin_5.pk),
            (plugin_6.pk, plugin_5.pk),
            (plugin_13.pk, plugin_5.pk),
            (plugin_14.pk, None),
        ]
        plugin_7 = self.reload(plugin_7)
        placeholder.move_plugin(
            plugin=self.reload(plugin_6),
            target_position=plugin_7.position,
            target_plugin=plugin_7.parent,
        )
        self.compare_plugin_tree(tree, placeholder)
        self.copy_placeholders_and_check_results([placeholder])

        # move plugin_3 before plugin_2
        tree = [
            (plugin_3.pk, None),
            (plugin_9.pk, plugin_3.pk),
            (plugin_2.pk, None),
            (plugin_12.pk, plugin_2.pk),
            (plugin_4.pk, plugin_2.pk),
            (plugin_10.pk, plugin_4.pk),
            (plugin_8.pk, plugin_2.pk),
            (plugin_11.pk, None),
            (plugin_1.pk, None),
            (plugin_5.pk, None),
            (plugin_7.pk, plugin_5.pk),
            (plugin_6.pk, plugin_5.pk),
            (plugin_13.pk, plugin_5.pk),
            (plugin_14.pk, None),
        ]
        placeholder.move_plugin(
            plugin=self.reload(plugin_3),
            target_position=1,
            target_plugin=None,
        )
        self.compare_plugin_tree(tree, placeholder)
        self.copy_placeholders_and_check_results([placeholder])

        # make plugin_3 plugin_2's first-child
        tree = [
            (plugin_2.pk, None),
            (plugin_3.pk, plugin_2.pk),
            (plugin_9.pk, plugin_3.pk),
            (plugin_12.pk, plugin_2.pk),
            (plugin_4.pk, plugin_2.pk),
            (plugin_10.pk, plugin_4.pk),
            (plugin_8.pk, plugin_2.pk),
            (plugin_11.pk, None),
            (plugin_1.pk, None),
            (plugin_5.pk, None),
            (plugin_7.pk, plugin_5.pk),
            (plugin_6.pk, plugin_5.pk),
            (plugin_13.pk, plugin_5.pk),
            (plugin_14.pk, None),
        ]
        placeholder.move_plugin(
            plugin=self.reload(plugin_3),
            target_position=2,
            target_plugin=self.reload(plugin_2),
        )
        self.compare_plugin_tree(tree, placeholder)
        self.copy_placeholders_and_check_results([placeholder])

        # make plugin_7 plugin_2's first-child
        tree = [
            (plugin_2.pk, None),
            (plugin_7.pk, plugin_2.pk),
            (plugin_3.pk, plugin_2.pk),
            (plugin_9.pk, plugin_3.pk),
            (plugin_12.pk, plugin_2.pk),
            (plugin_4.pk, plugin_2.pk),
            (plugin_10.pk, plugin_4.pk),
            (plugin_8.pk, plugin_2.pk),
            (plugin_11.pk, None),
            (plugin_1.pk, None),
            (plugin_5.pk, None),
            (plugin_6.pk, plugin_5.pk),
            (plugin_13.pk, plugin_5.pk),
            (plugin_14.pk, None),
        ]
        plugin_2 = self.reload(plugin_2)
        placeholder.move_plugin(
            plugin=self.reload(plugin_7),
            target_position=plugin_2.position + 1,
            target_plugin=plugin_2,
        )
        self.compare_plugin_tree(tree, placeholder)
        self.copy_placeholders_and_check_results([placeholder])

    def test_nested_plugin_on_page(self):
        """
        Validate a textplugin with a nested link plugin
        mptt values are correctly showing a parent child relationship
        of a nested plugin
        """
        with self.settings(CMS_PERMISSION=False):
            # setup page 1
            page_one = create_page("Three Placeholder", "col_three.html", "en",
                                   position="last-child", in_navigation=True)
            page_one_ph_two = page_one.get_placeholders("en").get(slot="col_left")

            # add a plugin
            pre_nesting_body = "<p>the nested text plugin with a link inside</p>"
            text_plugin = add_plugin(page_one_ph_two, "TextPlugin", "en", body=pre_nesting_body)
            # prepare nesting plugin
            page_one_ph_two = self.reload(page_one_ph_two)
            text_plugin = self.reload(text_plugin)
            link_plugin = add_plugin(page_one_ph_two, "LinkPlugin", "en", target=text_plugin)
            link_plugin.name = "django-cms Link"
            link_plugin.external_link = "https://www.django-cms.org"

            # reloading needs to be done after every save
            link_plugin = self.reload(link_plugin)
            text_plugin = self.reload(text_plugin)

            # mptt related insertion correct?
            msg = "parent plugin right is not updated, child not inserted correctly"
            self.assertTrue(link_plugin.position == text_plugin.position + 1, msg=msg)
            msg = "link has no parent"
            self.assertFalse(link_plugin.parent is None, msg=msg)

            # add the link plugin to the body
            # emulate the editor in admin that adds some txt for the nested plugin
            in_txt = '<img id="plugin_obj_%s" title="Link" alt="Link" src="/static/cms/img/icons/plugins/link.png">'
            nesting_body = "%s<p>%s</p>" % (text_plugin.body, (in_txt % (link_plugin.id)))
            text_plugin.body = nesting_body
            text_plugin.save()

            text_plugin = self.reload(text_plugin)
            # none of the descendants should have a placeholder other then my own one
            self.assertEqual(text_plugin.get_descendants().exclude(placeholder=text_plugin.placeholder).count(), 0)
            post_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(post_add_plugin_count, 2)

    def test_copy_page_nested_plugin(self):
        """
        Test to verify that page copy with a nested plugin works
        page one - 3 placeholder
                    col_sidebar: 1 text plugin
                    col_left: 1 text plugin with nested link plugin
                    col_right: no plugin
        page two (copy target)
        Verify copied page, placeholders, plugins and body text
        """
        with self.settings(CMS_PERMISSION=False):
            # setup page 1
            page_one = create_page("Three Placeholder", "col_three.html", "en",
                                   position="last-child", in_navigation=True)
            page_one_ph_one = page_one.get_placeholders("en").get(slot="col_sidebar")
            page_one_ph_two = page_one.get_placeholders("en").get(slot="col_left")
            page_one.get_placeholders("en").get(slot="col_right")
            # add the text plugin to placeholder one
            text_plugin_en = add_plugin(page_one_ph_one, "TextPlugin", "en", body="Hello World")
            self.assertEqual(text_plugin_en.id, CMSPlugin.objects.all()[0].id)
            self.assertEqual(text_plugin_en.get_children().count(), 0)
            pre_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(pre_add_plugin_count, 1)
            ###
            # add a plugin to placeholder two
            ###
            pre_nesting_body = "<p>the nested text plugin with a link inside</p>"
            text_plugin_two = add_plugin(page_one_ph_two, "TextPlugin", "en", body=pre_nesting_body)
            text_plugin_two = self.reload(text_plugin_two)
            # prepare nesting plugin
            page_one_ph_two = self.reload(page_one_ph_two)
            text_plugin_two = self.reload(text_plugin_two)
            link_plugin = add_plugin(page_one_ph_two, "LinkPlugin", "en", target=text_plugin_two)
            link_plugin.name = "django-cms Link"
            link_plugin.external_link = "https://www.django-cms.org"
            link_plugin.parent = text_plugin_two
            link_plugin.save()

            link_plugin = self.reload(link_plugin)
            text_plugin_two = self.reload(text_plugin_two)
            in_txt = """<cms-plugin id="%s" title="Link" alt="Link"></cms-plugin>"""
            nesting_body = "%s<p>%s</p>" % (text_plugin_two.body, (in_txt % (link_plugin.id)))
            # emulate the editor in admin that adds some txt for the nested plugin
            text_plugin_two.body = nesting_body
            text_plugin_two.save()
            text_plugin_two = self.reload(text_plugin_two)
            # the link is attached as a child?
            self.assertEqual(text_plugin_two.get_children().count(), 1)
            post_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(post_add_plugin_count, 3)
            page_one.save()
            # get the plugins from the original page
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.get_placeholders("en").get(slot="col_sidebar")
            page_one_ph_two = page_one.get_placeholders("en").get(slot="col_left")
            page_one_ph_three = page_one.get_placeholders("en").get(slot="col_right")
            # verify that the plugins got created
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEqual(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEqual(len(org_placeholder_two_plugins), 2)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEqual(len(org_placeholder_three_plugins), 0)
            self.assertEqual(page_one.get_placeholders("en").count(), 3)
            placeholder_count = Placeholder.objects.count()
            self.assertEqual(placeholder_count, 3)
            self.assertEqual(CMSPlugin.objects.count(), 3)
            ##
            # setup page_copy_target page
            ##
            page_copy_target = create_page("Three Placeholder - page copy target", "col_three.html", "en",
                                           position="last-child", in_navigation=True)
            all_page_count = Page.objects.count()
            pre_copy_placeholder_count = Placeholder.objects.count()
            self.assertEqual(pre_copy_placeholder_count, 6)
            # copy the page
            superuser = self.get_superuser()
            with self.login_user_context(superuser):
                page_two = self.copy_page(page_one, page_copy_target)
                # validate the expected pages,placeholders,plugins,pluginbodies
            after_copy_page_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(after_copy_page_plugin_count, 6)
            # check the amount of copied stuff
            after_copy_page_count = Page.objects.count()
            after_copy_placeholder_count = Placeholder.objects.count()
            self.assertGreater(after_copy_page_count, all_page_count, "no new page after copy")
            self.assertGreater(after_copy_page_plugin_count, post_add_plugin_count, "plugin count is not grown")
            self.assertGreater(after_copy_placeholder_count, pre_copy_placeholder_count,
                               "placeholder count is not grown")
            self.assertEqual(after_copy_page_count, 3, "no new page after copy")
            # original placeholder
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.get_placeholders("en").get(slot="col_sidebar")
            page_one_ph_two = page_one.get_placeholders("en").get(slot="col_left")
            page_one_ph_three = page_one.get_placeholders("en").get(slot="col_right")
            # check if there are multiple pages assigned to this placeholders
            found_page = page_one_ph_one.page if page_one_ph_one else None
            self.assertEqual(found_page, page_one)
            found_page = page_one_ph_two.page if page_one_ph_two else None
            self.assertEqual(found_page, page_one)
            found_page = page_one_ph_three.page if page_one_ph_three else None
            self.assertEqual(found_page, page_one)

            page_two = self.reload(page_two)
            page_two_ph_one = page_two.get_placeholders("en").get(slot="col_sidebar")
            page_two_ph_two = page_two.get_placeholders("en").get(slot="col_left")
            page_two_ph_three = page_two.get_placeholders("en").get(slot="col_right")
            # check if there are multiple pages assigned to this placeholders
            found_page = page_two_ph_one.page if page_two_ph_one else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_two.page if page_two_ph_two else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_three.page if page_two_ph_three else None
            self.assertEqual(found_page, page_two)
            # check the stored placeholders org vs copy
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_one.pk, page_one_ph_one.pk, page_two.pk)
            self.assertNotEqual(page_two_ph_one.pk, page_one_ph_one.pk, msg)
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_two.pk, page_one_ph_two.pk, page_two.pk)
            self.assertNotEqual(page_two_ph_two.pk, page_one_ph_two.pk, msg)
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_three.pk, page_one_ph_three.pk, page_two.pk)
            self.assertNotEqual(page_two_ph_three.pk, page_one_ph_three.pk, msg)
            # get the plugins from the original page
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEqual(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEqual(len(org_placeholder_two_plugins), 2)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEqual(len(org_placeholder_three_plugins), 0)
            # get the plugins from the copied page
            copied_placeholder_one_plugins = page_two_ph_one.get_plugins()
            self.assertEqual(len(copied_placeholder_one_plugins), 1)
            copied_placeholder_two_plugins = page_two_ph_two.get_plugins()
            self.assertEqual(len(copied_placeholder_two_plugins), 2)
            copied_placeholder_three_plugins = page_two_ph_three.get_plugins()
            self.assertEqual(len(copied_placeholder_three_plugins), 0)
            # verify the plugins got copied
            # placeholder 1
            count_plugins_copied = len(copied_placeholder_one_plugins)
            count_plugins_org = len(org_placeholder_one_plugins)
            msg = "plugin count %s %s for placeholder one not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # placeholder 2
            count_plugins_copied = len(copied_placeholder_two_plugins)
            count_plugins_org = len(org_placeholder_two_plugins)
            msg = "plugin count %s %s for placeholder two not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # placeholder 3
            count_plugins_copied = len(copied_placeholder_three_plugins)
            count_plugins_org = len(org_placeholder_three_plugins)
            msg = "plugin count %s %s for placeholder three not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # verify the body of text plugin with nested link plugin
            # org to copied
            org_nested_text_plugin = None
            # do this iteration to find the real text plugin with the attached link
            # the inheritance mechanism for the cmsplugins works through
            # (tuple)get_plugin_instance()
            for x in org_placeholder_two_plugins:
                if x.plugin_type == "TextPlugin":
                    instance = x.get_plugin_instance()[0]
                    if instance.body.startswith(pre_nesting_body):
                        org_nested_text_plugin = instance
                        break
            copied_nested_text_plugin = None
            for x in copied_placeholder_two_plugins:
                if x.plugin_type == "TextPlugin":
                    instance = x.get_plugin_instance()[0]
                    if instance.body.startswith(pre_nesting_body):
                        copied_nested_text_plugin = instance
                        break
            msg = "original nested text plugin not found"
            self.assertNotEqual(org_nested_text_plugin, None, msg=msg)
            msg = "copied nested text plugin not found"
            self.assertNotEqual(copied_nested_text_plugin, None, msg=msg)
            # get the children ids of the texplugin with a nested link
            # to check if the body of the text is generated correctly
            org_link_child_plugin = org_nested_text_plugin.get_children()[0]
            copied_link_child_plugin = copied_nested_text_plugin.get_children()[0]
            # validate the textplugin body texts
            msg = "org plugin and copied plugin are the same"
            self.assertTrue(org_link_child_plugin.id != copied_link_child_plugin.id, msg)
            needle = "%s"
            msg = "child plugin id differs to parent in body"
            # linked child is in body
            self.assertTrue(org_nested_text_plugin.body.find(needle % (org_link_child_plugin.id)) != -1, msg)
            msg = "copy: child plugin id differs to parent in body"
            self.assertTrue(copied_nested_text_plugin.body.find(needle % (copied_link_child_plugin.id)) != -1, msg)
            # really nothing else
            msg = "child link plugin id differs to parent body"
            self.assertTrue(org_nested_text_plugin.body.find(needle % (copied_link_child_plugin.id)) == -1, msg)
            msg = "copy: child link plugin id differs to parent body"
            self.assertTrue(copied_nested_text_plugin.body.find(needle % (org_link_child_plugin.id)) == -1, msg)
            # now reverse lookup the placeholders from the plugins
            org_placeholder = org_link_child_plugin.placeholder
            copied_placeholder = copied_link_child_plugin.placeholder
            msg = "placeholder of the original plugin and copied plugin are the same"
            ok = (org_placeholder.id != copied_placeholder.id)
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
        with self.settings(CMS_PERMISSION=False):
            # setup page 1
            page_one = create_page("Three Placeholder", "col_three.html", "en",
                                   position="last-child", in_navigation=True)
            page_one_ph_one = page_one.get_placeholders("en").get(slot="col_sidebar")
            page_one_ph_two = page_one.get_placeholders("en").get(slot="col_left")
            page_one.get_placeholders("en").get(slot="col_right")
            # add the text plugin to placeholder one
            text_plugin_en = add_plugin(page_one_ph_one, "TextPlugin", "en", body="Hello World")
            self.assertEqual(text_plugin_en.id, CMSPlugin.objects.all()[0].id)
            self.assertEqual(text_plugin_en.get_children().count(), 0)
            pre_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(pre_add_plugin_count, 1)
            # add a plugin to placeholder twho
            pre_nesting_body = "<p>the nested text plugin with a link inside</p>"
            text_plugin_two = add_plugin(page_one_ph_two, "TextPlugin", "en", body=pre_nesting_body)
            text_plugin_two = self.reload(text_plugin_two)
            # prepare nesting plugin
            page_one_ph_two = self.reload(page_one_ph_two)
            text_plugin_two = self.reload(text_plugin_two)
            link_plugin = add_plugin(page_one_ph_two, "LinkPlugin", "en", target=text_plugin_two)
            link_plugin.name = "django-cms Link"
            link_plugin.external_link = "https://www.django-cms.org"
            link_plugin.parent = text_plugin_two
            link_plugin.save()
            # reload after every save
            link_plugin = self.reload(link_plugin)
            text_plugin_two = self.reload(text_plugin_two)
            in_txt = """<cms-plugin id="%s" title="Link" alt="Link"></cms-plugin>"""
            nesting_body = "%s<p>%s</p>" % (text_plugin_two.body, (in_txt % (link_plugin.id)))
            # emulate the editor in admin that adds some txt for the nested plugin
            text_plugin_two.body = nesting_body
            text_plugin_two.save()
            text_plugin_two = self.reload(text_plugin_two)
            # the link is attached as a child?
            self.assertEqual(text_plugin_two.get_children().count(), 1)
            post_add_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(post_add_plugin_count, 3)
            page_one.save()
            # get the plugins from the original page
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.get_placeholders("en").get(slot="col_sidebar")
            page_one_ph_two = page_one.get_placeholders("en").get(slot="col_left")
            page_one_ph_three = page_one.get_placeholders("en").get(slot="col_right")
            # verify the plugins got created
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEqual(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEqual(len(org_placeholder_two_plugins), 2)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEqual(len(org_placeholder_three_plugins), 0)
            self.assertEqual(page_one.get_placeholders("en").count(), 3)

            placeholder_count = Placeholder.objects.count()
            self.assertEqual(placeholder_count, 3)
            self.assertEqual(CMSPlugin.objects.count(), 3)
            # setup page_copy_target
            page_copy_target = create_page("Three Placeholder - page copy target", "col_three.html", "en",
                                           position="last-child", in_navigation=True)
            all_page_count = Page.objects.count()
            pre_copy_placeholder_count = Placeholder.objects.count()
            self.assertEqual(pre_copy_placeholder_count, 6)
            superuser = self.get_superuser()

            with self.login_user_context(superuser):
                # now move the parent text plugin to another placeholder
                post_data = {
                    'placeholder_id': page_one_ph_three.id,
                    'plugin_id': text_plugin_two.id,
                    'target_language': 'en',
                    'target_position': page_one_ph_three.get_next_plugin_position('en', insert_order='last'),
                    'plugin_parent': '',

                }
                edit_url = self.get_move_plugin_uri(text_plugin_two)
                response = self.client.post(edit_url, post_data)
                self.assertEqual(response.status_code, 200)
                # check if the plugin got moved
                page_one = self.reload(page_one)
                self.reload(text_plugin_two)
                page_one_ph_one = page_one.get_placeholders("en").get(slot="col_sidebar")
                page_one_ph_two = page_one.get_placeholders("en").get(slot="col_left")
                page_one_ph_three = page_one.get_placeholders("en").get(slot="col_right")

                org_placeholder_one_plugins = page_one_ph_one.get_plugins()
                self.assertEqual(len(org_placeholder_one_plugins), 1)
                org_placeholder_two_plugins = page_one_ph_two.get_plugins()
                # the plugin got moved and child got moved
                self.assertEqual(len(org_placeholder_two_plugins), 0)
                org_placeholder_three_plugins = page_one_ph_three.get_plugins()
                self.assertEqual(len(org_placeholder_three_plugins), 2)
                # copy the page
                page_two = self.copy_page(page_one, page_copy_target)
                # validate the expected pages,placeholders,plugins,pluginbodies
            after_copy_page_plugin_count = CMSPlugin.objects.count()
            self.assertEqual(after_copy_page_plugin_count, 6)
            after_copy_page_count = Page.objects.count()
            after_copy_placeholder_count = Placeholder.objects.count()
            self.assertGreater(after_copy_page_count, all_page_count, "no new page after copy")
            self.assertGreater(after_copy_page_plugin_count, post_add_plugin_count, "plugin count is not grown")
            self.assertGreater(after_copy_placeholder_count, pre_copy_placeholder_count,
                               "placeholder count is not grown")
            self.assertEqual(after_copy_page_count, 3, "no new page after copy")
            # validate the structure
            # original placeholder
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.get_placeholders("en").get(slot="col_sidebar")
            page_one_ph_two = page_one.get_placeholders("en").get(slot="col_left")
            page_one_ph_three = page_one.get_placeholders("en").get(slot="col_right")
            # check if there are multiple pages assigned to this placeholders
            found_page = page_one_ph_one.page if page_one_ph_one else None
            self.assertEqual(found_page, page_one)
            found_page = page_one_ph_two.page if page_one_ph_two else None
            self.assertEqual(found_page, page_one)
            found_page = page_one_ph_three.page if page_one_ph_three else None
            self.assertEqual(found_page, page_one)
            page_two = self.reload(page_two)
            page_two_ph_one = page_two.get_placeholders("en").get(slot="col_sidebar")
            page_two_ph_two = page_two.get_placeholders("en").get(slot="col_left")
            page_two_ph_three = page_two.get_placeholders("en").get(slot="col_right")
            # check if there are multiple pages assigned to this placeholders
            found_page = page_two_ph_one.page if page_two_ph_one else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_two.page if page_two_ph_two else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_three.page if page_two_ph_three else None
            self.assertEqual(found_page, page_two)
            # check the stored placeholders org vs copy
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_one.pk, page_one_ph_one.pk, page_two.pk)
            self.assertNotEqual(page_two_ph_one.pk, page_one_ph_one.pk, msg)
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_two.pk, page_one_ph_two.pk, page_two.pk)
            self.assertNotEqual(page_two_ph_two.pk, page_one_ph_two.pk, msg)
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_three.pk, page_one_ph_three.pk, page_two.pk)
            self.assertNotEqual(page_two_ph_three.pk, page_one_ph_three.pk, msg)
            # get the plugins from the original page
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEqual(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEqual(len(org_placeholder_two_plugins), 0)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEqual(len(org_placeholder_three_plugins), 2)
            # get the plugins from the copied page
            copied_placeholder_one_plugins = page_two_ph_one.get_plugins()
            self.assertEqual(len(copied_placeholder_one_plugins), 1)
            copied_placeholder_two_plugins = page_two_ph_two.get_plugins()
            self.assertEqual(len(copied_placeholder_two_plugins), 0)
            copied_placeholder_three_plugins = page_two_ph_three.get_plugins()
            self.assertEqual(len(copied_placeholder_three_plugins), 2)
            # verify the plugins got copied
            # placeholder 1
            count_plugins_copied = len(copied_placeholder_one_plugins)
            count_plugins_org = len(org_placeholder_one_plugins)
            msg = "plugin count %s %s for placeholder one not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # placeholder 2
            count_plugins_copied = len(copied_placeholder_two_plugins)
            count_plugins_org = len(org_placeholder_two_plugins)
            msg = "plugin count %s %s for placeholder two not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # placeholder 3
            count_plugins_copied = len(copied_placeholder_three_plugins)
            count_plugins_org = len(org_placeholder_three_plugins)
            msg = "plugin count %s %s for placeholder three not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # verify the body of text plugin with nested link plugin
            # org to copied
            org_nested_text_plugin = None
            # do this iteration to find the real text plugin with the attached link
            # the inheritance mechanism for the cmsplugins works through
            # (tuple)get_plugin_instance()
            for x in org_placeholder_three_plugins:
                if x.plugin_type == "TextPlugin":
                    instance = x.get_plugin_instance()[0]
                    if instance.body.startswith(pre_nesting_body):
                        org_nested_text_plugin = instance
                        break
            copied_nested_text_plugin = None
            for x in copied_placeholder_three_plugins:
                if x.plugin_type == "TextPlugin":
                    instance = x.get_plugin_instance()[0]
                    if instance.body.startswith(pre_nesting_body):
                        copied_nested_text_plugin = instance
                        break
            msg = "original nested text plugin not found"
            self.assertNotEqual(org_nested_text_plugin, None, msg=msg)
            msg = "copied nested text plugin not found"
            self.assertNotEqual(copied_nested_text_plugin, None, msg=msg)
            # get the children ids of the texplugin with a nested link
            # to check if the body of the text is generated correctly
            org_link_child_plugin = org_nested_text_plugin.get_children()[0]
            copied_link_child_plugin = copied_nested_text_plugin.get_children()[0]
            # validate the textplugin body texts
            msg = "org plugin and copied plugin are the same"
            self.assertNotEqual(org_link_child_plugin.id, copied_link_child_plugin.id, msg)
            needle = "%s"
            msg = "child plugin id differs to parent in body"
            # linked child is in body
            self.assertTrue(org_nested_text_plugin.body.find(needle % (org_link_child_plugin.id)) != -1, msg)
            msg = "copy: child plugin id differs to parent in body plugin_obj_id"
            self.assertTrue(copied_nested_text_plugin.body.find(needle % (copied_link_child_plugin.id)) != -1, msg)
            # really nothing else
            msg = "child link plugin id differs to parent body"
            self.assertTrue(org_nested_text_plugin.body.find(needle % (copied_link_child_plugin.id)) == -1, msg)
            msg = "copy: child link plugin id differs to parent body"
            self.assertTrue(copied_nested_text_plugin.body.find(needle % (org_link_child_plugin.id)) == -1, msg)
            # now reverse lookup the placeholders from the plugins
            org_placeholder = org_link_child_plugin.placeholder
            copied_placeholder = copied_link_child_plugin.placeholder
            msg = "placeholder of the original plugin and copied plugin are the same"
            self.assertNotEqual(org_placeholder.id, copied_placeholder.id, msg)

    def test_add_child_plugin(self):
        page_one = create_page("Three Placeholder", "col_three.html", "en",
                               position="last-child", in_navigation=True)
        page_one_ph_one = page_one.get_placeholders("en").get(slot="col_sidebar")
        # add the text plugin to placeholder one
        text_plugin_en = add_plugin(page_one_ph_one, "TextPlugin", "en", body="Hello World")
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            post_data = {
                'name': 'test',
                'external_link': 'http://www.example.org/'
            }
            add_url = self.get_add_plugin_uri(page_one_ph_one, 'LinkPlugin', parent=text_plugin_en)
            response = self.client.post(add_url, post_data)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(
                response,
                'admin/cms/page/plugin/confirm_form.html'
            )
        link_plugin = CMSPlugin.objects.get(parent_id=text_plugin_en.pk)
        self.assertEqual(link_plugin.parent_id, text_plugin_en.pk)
        self.assertEqual(link_plugin.position, text_plugin_en.position + 1)

    def test_plugin_deep_nesting_and_copying_issue_position_parent_child_discrepency(self):
        """
        Captures an edge case issue where plugins have been seen to have a higher
        position than their parent. When the placeholder is
        copied the parent defaults to None because the plugin is not yet created / remapped.

        Plugins first created in this order:

            Plugin 1 (pk1, position 1)
            Plugin 2 (pk2, position 2)
            Plugin 3 (pk3, position 3)

        Then a top level plugin is made a child of another.
        The result is a child with a lower id and higher position that it's parent.

            Plugin 1 (pk1, position 1)
            Plugin 3 has children (pk3, position 3)
                Plugin 2 (pk2, position 2)
        """
        placeholder = Placeholder(slot="some_slot")
        placeholder.save()
        # plugins in placeholder
        plugin_1 = add_plugin(placeholder, "TextPlugin", "en", body="01")
        plugin_2 = add_plugin(placeholder, "TextPlugin", "en", body="02")
        plugin_3 = add_plugin(placeholder, "TextPlugin", "en", body="03")

        expected_tree = [
            (plugin_1.pk, None),
            (plugin_2.pk, None),
            (plugin_3.pk, None),
        ]

        self.copy_placeholders_and_check_results([placeholder])
        self.compare_plugin_tree(expected_tree, placeholder)

        plugin_2.parent = plugin_3
        plugin_2.save()

        self.reload(plugin_2)
        self.reload(plugin_3)

        expected_tree = [
            (plugin_1.pk, None),
            (plugin_2.pk, plugin_3.pk),
            (plugin_3.pk, None),
        ]

        placeholder._recalculate_plugin_positions("en")

        self.copy_placeholders_and_check_results([placeholder])
        self.compare_plugin_tree(expected_tree, placeholder)
