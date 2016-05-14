# -*- coding: utf-8 -*-
import json
from django.utils.http import urlencode

from djangocms_text_ckeditor.models import Text

from cms.api import create_page, add_plugin
from cms.constants import PLUGIN_MOVE_ACTION
from cms.models import Page
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.tests.test_plugins import PluginsTestBaseCase
from cms.test_utils.testcases import URL_CMS_PLUGIN_PAGE_MOVE, URL_CMS_PLUGIN_PAGE_ADD
from cms.utils.compat.tests import UnittestCompatMixin
from cms.utils.copy_plugins import copy_plugins_to
from cms.utils.i18n import force_language
from cms.utils.plugins import reorder_plugins


class NestedPluginsTestCase(PluginsTestBaseCase, UnittestCompatMixin):

    def reorder_positions(self, plugin=None, parent=None):

        if parent:
            parent_id = parent.pk
            plugin = parent
        else:
            parent_id = plugin.parent_id
        x = 0
        for p in CMSPlugin.objects.filter(parent_id=parent_id, language=plugin.language, placeholder_id=plugin.placeholder_id):
            p.position = x
            p.save()
            x += 1

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
            copy_plugins_to(
                original_placeholder.get_plugins(),
                copied_placeholder
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

            # Now build a *tree* of the plugins, and match those - it's not
            # enough just to compare querysets as above; we should *also* check
            # that when we build a tree, the various nodes are assembled as we
            # would expect. We will pump the trees into a pair of lists:
            original_plugins_list = []
            copied_plugins_list = []

            # This function builds the tree of plugins, starting from its roots.
            # In that respect it's like many of the plugin tree-building
            # routines elsewhere in the system.
            def plugin_list_from_tree(roots, plugin_list):
                for plugin in roots:
                    plugin_list.append(plugin)
                    # recurse over the set of nodes
                    plugin_list_from_tree(plugin.get_children(), plugin_list)

            # build the tree for each set of plugins
            plugin_list_from_tree(original_plugins.filter(depth=1), original_plugins_list)
            plugin_list_from_tree(copied_plugins.filter(depth=1), copied_plugins_list)

            self.assertEqual(len(original_plugins_list), original_plugins.count())
            self.assertEqual(len(copied_plugins_list), copied_plugins.count())
            # Check that each pair of items in the two lists match, in lots of
            # different ways
            for original, copy in zip(original_plugins_list, copied_plugins_list):
                original_text_plugin = Text.objects.get(id=original.id)
                copied_text_plugin = Text.objects.get(id=copy.id)

                # This first one is a sanity test, just to prove that we aren't
                # simply comparing *exactly the same items* in all these tests.
                # It could happen...
                self.assertNotEquals(original.id, copy.id)
                self.assertEqual(
                    original_text_plugin.body,
                    copied_text_plugin.body
                )
                self.assertEqual(
                    original_text_plugin.depth,
                    copied_text_plugin.depth
                )
                self.assertEqual(
                    original_text_plugin.position,
                    copied_text_plugin.position
                )
                self.assertEqual(
                    original_text_plugin.numchild,
                    copied_text_plugin.numchild
                )

                self.assertEqual(
                    original_text_plugin.get_descendant_count(),
                    copied_text_plugin.get_descendant_count()
                )
                self.assertEqual(
                    original_text_plugin.get_ancestors().count(),
                    copied_text_plugin.get_ancestors().count()
                )

        # just in case the test method that called us wants it:
        return copied_placeholder

    def test_plugin_fix_tree(self):
        """
        Tests CMSPlugin.fix_tree by creating a plugin structure, setting the
        position value to Null for all the plugins and then rebuild the tree.

        The structure below isn't arbitrary, but has been designed to test
        various conditions, including:

        * nodes four levels deep
        * siblings with and without children

             1
                 2
                     4
                          10
                     8
                 3
                     9
             5
                 6
                 7
        """

        placeholder = Placeholder(slot=u"some_slot")
        placeholder.save()  # a good idea, if not strictly necessary

        # plugin in placeholder
        plugin_1 = add_plugin(placeholder, u"TextPlugin", u"en", body=u"01")

        # IMPORTANT: plugins must be reloaded, before they can be assigned
        # as a parent. Otherwise, the Tree structure doesn't seem to rebuild
        # properly.

        # child of plugin_1
        plugin_1 = self.reload(plugin_1)
        plugin_2 = add_plugin(placeholder, u"TextPlugin", u"en",  # nopyflakes
                              body=u"02", target=plugin_1,
        )

        # create a second child of plugin_1
        plugin_1 = self.reload(plugin_1)
        plugin_3 = add_plugin(placeholder, u"TextPlugin", u"en",  # nopyflakes
                              body=u"03", target=plugin_1
        )

        # child of plugin_2
        plugin_2 = self.reload(plugin_2)
        plugin_4 = add_plugin(placeholder, u"TextPlugin", u"en",  # nopyflakes
                              body=u"04", target=plugin_2
        )


        plugin_1 = self.reload(plugin_1)  # nopyflakes
        # create a second root plugin
        plugin_5 = add_plugin(placeholder, u"TextPlugin", u"en", body=u"05")
        left = CMSPlugin.objects.filter(parent__isnull=True).order_by('path')[0]
        plugin_5 = self.reload(plugin_5)
        plugin_5 = plugin_5.move(left, pos='right')
        self.reorder_positions(plugin_5)
        self.reorder_positions(plugin_2)

        # child of plugin_5
        plugin_5 = self.reload(plugin_5)
        plugin_6 = add_plugin(placeholder, u"TextPlugin", u"en",  # nopyflakes
                              body=u"06", target=plugin_5
        )

        # child of plugin_6
        plugin_5 = self.reload(plugin_5)
        plugin_7 = add_plugin(placeholder, u"TextPlugin", u"en",  # nopyflakes
                              body=u"07", target=plugin_5
        )

        # another child of plugin_2
        plugin_2 = self.reload(plugin_2)
        plugin_8 = add_plugin(placeholder, u"TextPlugin", u"en",  # nopyflakes
                              body=u"08", target=plugin_2
        )

        # child of plugin_3
        plugin_3 = self.reload(plugin_3)
        plugin_9 = add_plugin(placeholder, u"TextPlugin", u"en",  # nopyflakes
                              body=u"09", target=plugin_3
        )

        # child of plugin_4
        plugin_4 = self.reload(plugin_4)
        plugin_10 = add_plugin(placeholder, u"TextPlugin", u"en",  # nopyflakes
                               body=u"10", target=plugin_4
        )

        # We do two comparisons here.
        # One is to compare plugin position values
        # per plugin instance.
        # To do this we get a dictionary mapping plugin
        # ids to their respective position.
        # The second comparison is to make sure that
        # plugins retain their position/path ordering.

        # The reason for the these comparisons
        # is because of an obscure behavior with postgres
        # where somehow items with the same value that are
        # sorted by that value will be returned in different
        # order based on the orm query construction.

        # By comparing ids with positions, we make sure that
        # each plugin has the correct position after the fix-tree.
        # See ticket #5291
        plugins = (
            CMSPlugin
            .objects
            .filter(placeholder=placeholder)
        )

        # Maps plugin ids to positions
        original_plugin_positions = dict(
            plugins
            .order_by('position')
            .values_list('pk', 'position')
        )

        # List of plugin ids sorted by position and path
        original_plugin_ids = list(
            plugins
            .order_by('position', 'path')
            .values_list('pk', flat=True)
        )

        # We use 1 to effectively "break" the tree
        # and as a way to test that fixing trees with
        # equal position values retains the correct ordering.
        CMSPlugin.objects.update(position=1)
        CMSPlugin.fix_tree()

        new_plugin_positions = dict(
            plugins
            .order_by('position')
            .values_list('pk', 'position')
        )

        new_plugin_ids = list(
            plugins
            .order_by('position', 'path')
            .values_list('pk', flat=True)
        )

        self.assertDictEqual(original_plugin_positions, new_plugin_positions)
        self.assertSequenceEqual(original_plugin_ids, new_plugin_ids)

        # Now, check to see if the correct order is restored, even if we
        # re-arrange the plugins so that their natural «pk» order is different
        # than their «position» order.

        # Move the 2nd top-level plugin to the "left" or before the 1st.
        reorder_plugins(placeholder, None, u"en", [plugin_5.pk, plugin_1.pk])
        reordered_plugins = list(placeholder.get_plugins().order_by('position', 'path'))
        CMSPlugin.fix_tree()

        # Now, they should NOT be in the original order at all. Are they?
        new_plugins = list(placeholder.get_plugins().order_by('position', 'path'))
        self.assertSequenceEqual(
            reordered_plugins, new_plugins,
            "Plugin order not preserved during fix_tree().")


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

        placeholder = Placeholder(slot=u"some_slot")
        placeholder.save()  # a good idea, if not strictly necessary

        # plugin in placeholder
        plugin_1 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"01")

        # IMPORTANT: plugins must be reloaded, before they can be assigned
        # as a parent. Otherwise, the MPTT structure doesn't seem to rebuild
        # properly.

        # child of plugin_1
        plugin_1 = self.reload(plugin_1)
        plugin_2 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"02", target=plugin_1,
        )
        # plugin_2 should be plugin_1's only child
        # for a single item we use assertSequenceEqual
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_1.pk).get_children(),
            [CMSPlugin.objects.get(id=plugin_2.pk)])

        # create a second child of plugin_1
        plugin_1 = self.reload(plugin_1)
        plugin_3 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"03", target=plugin_1
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
        plugin_2 = self.reload(plugin_2)
        plugin_4 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"04", target=plugin_2
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
        plugin_1 = self.reload(plugin_1)
        # create a second root plugin
        plugin_5 = add_plugin(placeholder, u"TextPlugin", u"en", body=u"05")
        left = CMSPlugin.objects.filter(parent__isnull=True).order_by('path')[0]
        plugin_5 = self.reload(plugin_5)
        plugin_5 = plugin_5.move(left, pos='right')
        self.reorder_positions(plugin_5)
        self.reorder_positions(plugin_2)

        # child of plugin_5
        plugin_5 = self.reload(plugin_5)
        plugin_6 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"06", target=plugin_5
        )


        # plugin_6 should be plugin_5's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_5.pk).get_children(),
            [CMSPlugin.objects.get(id=plugin_6.pk)])

        # child of plugin_6
        plugin_5 = self.reload(plugin_5)
        plugin_7 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"07", target=plugin_5
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
        plugin_8 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"08", target=plugin_2
        )

        # plugin_4 should be plugin_2's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_2.pk).get_children(),
            [
                CMSPlugin.objects.get(id=plugin_4.pk),
                CMSPlugin.objects.get(id=plugin_8.pk),
            ])

        # child of plugin_3
        plugin_3 = self.reload(plugin_3)
        plugin_9 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"09", target=plugin_3
        )

        # plugin_9 should be plugin_3's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_3.pk).get_children(),
            [CMSPlugin.objects.get(id=plugin_9.pk)])

        # child of plugin_4
        plugin_4 = self.reload(plugin_4)
        plugin_10 = add_plugin(placeholder, u"TextPlugin", u"en",
                               body=u"10", target=plugin_4
        )

        # plugin_10 should be plugin_4's child
        self.assertSequenceEqual(
            CMSPlugin.objects.get(id=plugin_4.pk).get_children(),
            [CMSPlugin.objects.get(id=plugin_10.pk)])

        original_plugins = placeholder.get_plugins()
        self.assertEqual(original_plugins.count(), 10)

        # elder sibling of plugin_1
        plugin_1 = self.reload(plugin_1)
        plugin_11 = add_plugin(placeholder, u"TextPlugin", u"en",
                               body=u"11",
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
        plugin_4 = self.reload(plugin_4)
        plugin_12 = add_plugin(placeholder, u"TextPlugin", u"en",
                               body=u"12",
                               target=plugin_4,
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
        plugin_7 = self.reload(plugin_7)
        plugin_13 = add_plugin(placeholder, u"TextPlugin", u"en",
                               body=u"13",
                               target=plugin_7,
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
        plugin_5 = self.reload(plugin_5)
        plugin_14 = add_plugin(placeholder, u"TextPlugin", u"en",
                               body=u"14"
        )

        self.assertSequenceEqual(
            CMSPlugin.objects.filter(depth=1).order_by('path'),
            [
                CMSPlugin.objects.get(id=plugin_11.pk),
                CMSPlugin.objects.get(id=plugin_1.pk),
                CMSPlugin.objects.get(id=plugin_5.pk),
                CMSPlugin.objects.get(id=plugin_14.pk)
            ])

        self.copy_placeholders_and_check_results([placeholder])

        # now let's move plugins around in the tree

        # move plugin_2 before plugin_11
        plugin_2 = self.reload(plugin_2)
        plugin_1 = self.reload(plugin_1)
        old_parent = plugin_2.parent
        plugin_2.parent_id = plugin_1.parent_id
        plugin_2.save()
        plugin_2 = plugin_2.move(target=plugin_1, pos="left")
        self.reorder_positions(parent=old_parent)
        self.reorder_positions(plugin_2)
        self.copy_placeholders_and_check_results([placeholder])

        # move plugin_6 after plugin_7
        plugin_6 = self.reload(plugin_6)
        plugin_7 = self.reload(plugin_7)
        old_parent = plugin_6.parent
        plugin_6.parent_id = plugin_7.parent_id
        plugin_6.save()
        plugin_6 = plugin_6.move(target=plugin_7, pos="right")
        self.reorder_positions(parent=old_parent)
        self.reorder_positions(plugin_6)
        self.copy_placeholders_and_check_results([placeholder])

        # move plugin_3 before plugin_2
        plugin_2 = self.reload(plugin_2)
        plugin_3 = self.reload(plugin_3)
        old_parent = plugin_3.parent
        plugin_3.parent_id = plugin_2.parent_id
        plugin_3.save()
        plugin_3 = plugin_3.move(target=plugin_2, pos="left")
        self.reorder_positions(parent=old_parent)
        self.reorder_positions(plugin_3)
        self.copy_placeholders_and_check_results([placeholder])

        # make plugin_3 plugin_2's first-child
        plugin_2 = self.reload(plugin_2)
        plugin_3 = self.reload(plugin_3)
        old_parent = plugin_3.parent
        plugin_3.parent_id = plugin_2.pk
        plugin_3.save()
        plugin_3 = plugin_3.move(target=plugin_2, pos="first-child")
        self.reorder_positions(CMSPlugin.objects.filter(placeholder_id=plugin_3.placeholder_id, language=plugin_3.language, depth=1)[0])
        self.reorder_positions(plugin_3)
        self.copy_placeholders_and_check_results([placeholder])

        # make plugin_7 plugin_2's first-child
        plugin_3 = self.reload(plugin_3)
        plugin_7 = self.reload(plugin_7)
        old_parent = plugin_7.parent
        plugin_7.parent_id = plugin_3.parent_id
        plugin_7.save()
        plugin_7 = plugin_7.move(target=plugin_3, pos="right")
        self.reorder_positions(parent=old_parent)
        self.reorder_positions(plugin_7)
        self.copy_placeholders_and_check_results([placeholder, ])

    def test_nested_plugin_on_page(self):
        """
        Validate a textplugin with a nested link plugin
        mptt values are correctly showing a parent child relationship
        of a nested plugin
        """
        with self.settings(CMS_PERMISSION=False):
            # setup page 1
            page_one = create_page(u"Three Placeholder", u"col_three.html", u"en",
                                   position=u"last-child", published=True, in_navigation=True)
            page_one_ph_two = page_one.placeholders.get(slot=u"col_left")

            # add a plugin
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
            self.assertTrue(text_plugin.position == link_plugin.position, msg=msg)
            msg = u"link has no parent"
            self.assertFalse(link_plugin.parent is None, msg=msg)
            msg = u"parent plugin path is not updated, child not inserted correctly"
            self.assertTrue(text_plugin.path == link_plugin.path[:4], msg=msg)
            msg = u"child level is not bigger than parent level"
            self.assertTrue(text_plugin.depth < link_plugin.depth, msg=msg)

            # add the link plugin to the body
            # emulate the editor in admin that adds some txt for the nested plugin
            in_txt = u"""<img id="plugin_obj_%s" title="Link" alt="Link" src="/static/cms/img/icons/plugins/link.png">"""
            nesting_body = u"%s<p>%s</p>" % (text_plugin.body, (in_txt % (link_plugin.id)))
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
            page_one = create_page(u"Three Placeholder", u"col_three.html", u"en",
                                   position=u"last-child", published=True, in_navigation=True)
            page_one_ph_one = page_one.placeholders.get(slot=u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot=u"col_left")
            page_one.placeholders.get(slot=u"col_right")
            # add the text plugin to placeholder one
            text_plugin_en = add_plugin(page_one_ph_one, u"TextPlugin", u"en", body="Hello World")
            self.assertEqual(text_plugin_en.id, CMSPlugin.objects.all()[0].id)
            self.assertEqual(text_plugin_en.get_children().count(), 0)
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
            in_txt = """<img id="plugin_obj_%s" title="Link" alt="Link" src="/static/cms/img/icons/plugins/link.png">"""
            nesting_body = "%s<p>%s</p>" % (text_plugin_two.body, (in_txt % (link_plugin.id)))
            # emulate the editor in admin that adds some txt for the nested plugin
            text_plugin_two.body = nesting_body
            text_plugin_two.save()
            text_plugin_two = self.reload(text_plugin_two)
            # the link is attached as a child?
            self.assertEqual(text_plugin_two.get_children().count(), 1)
            post_add_plugin_count = CMSPlugin.objects.filter(placeholder__page__publisher_is_draft=True).count()
            self.assertEqual(post_add_plugin_count, 3)
            page_one.save()
            # get the plugins from the original page
            page_one = self.reload(page_one)
            page_one_ph_one = page_one.placeholders.get(slot=u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot=u"col_left")
            page_one_ph_three = page_one.placeholders.get(slot=u"col_right")
            # verify that the plugins got created
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEqual(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEqual(len(org_placeholder_two_plugins), 2)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEqual(len(org_placeholder_three_plugins), 0)
            self.assertEqual(page_one.placeholders.count(), 3)
            placeholder_count = Placeholder.objects.filter(page__publisher_is_draft=True).count()
            self.assertEqual(placeholder_count, 3)
            self.assertEqual(CMSPlugin.objects.filter(placeholder__page__publisher_is_draft=True).count(), 3)
            ##
            # setup page_copy_target page
            ##
            page_copy_target = create_page("Three Placeholder - page copy target", "col_three.html", "en",
                                           position="last-child", published=True, in_navigation=True)
            all_page_count = Page.objects.drafts().count()
            pre_copy_placeholder_count = Placeholder.objects.filter(page__publisher_is_draft=True).count()
            self.assertEqual(pre_copy_placeholder_count, 6)
            # copy the page
            superuser = self.get_superuser()
            with self.login_user_context(superuser):
                page_two = self.copy_page(page_one, page_copy_target)
                # validate the expected pages,placeholders,plugins,pluginbodies
            after_copy_page_plugin_count = CMSPlugin.objects.filter(placeholder__page__publisher_is_draft=True).count()
            self.assertEqual(after_copy_page_plugin_count, 6)
            # check the amount of copied stuff
            after_copy_page_count = Page.objects.drafts().count()
            after_copy_placeholder_count = Placeholder.objects.filter(page__publisher_is_draft=True).count()
            self.assertGreater(after_copy_page_count, all_page_count, u"no new page after copy")
            self.assertGreater(after_copy_page_plugin_count, post_add_plugin_count, u"plugin count is not grown")
            self.assertGreater(after_copy_placeholder_count, pre_copy_placeholder_count,
                               u"placeholder count is not grown")
            self.assertEqual(after_copy_page_count, 3, u"no new page after copy")
            # original placeholder
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
            page_two_ph_one = page_two.placeholders.get(slot=u"col_sidebar")
            page_two_ph_two = page_two.placeholders.get(slot=u"col_left")
            page_two_ph_three = page_two.placeholders.get(slot=u"col_right")
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
            self.assertNotEquals(page_two_ph_one.pk, page_one_ph_one.pk, msg)
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_two.pk, page_one_ph_two.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_two.pk, page_one_ph_two.pk, msg)
            msg = 'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_three.pk, page_one_ph_three.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_three.pk, page_one_ph_three.pk, msg)
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
            msg = u"plugin count %s %s for placeholder one not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # placeholder 2
            count_plugins_copied = len(copied_placeholder_two_plugins)
            count_plugins_org = len(org_placeholder_two_plugins)
            msg = u"plugin count %s %s for placeholder two not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # placeholder 3
            count_plugins_copied = len(copied_placeholder_three_plugins)
            count_plugins_org = len(org_placeholder_three_plugins)
            msg = u"plugin count %s %s for placeholder three not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
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
        with self.settings(CMS_PERMISSION=False):
            # setup page 1
            page_one = create_page(u"Three Placeholder", u"col_three.html", u"en",
                                   position=u"last-child", published=True, in_navigation=True)
            page_one_ph_one = page_one.placeholders.get(slot=u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot=u"col_left")
            page_one.placeholders.get(slot=u"col_right")
            # add the text plugin to placeholder one
            text_plugin_en = add_plugin(page_one_ph_one, u"TextPlugin", u"en", body=u"Hello World")
            self.assertEqual(text_plugin_en.id, CMSPlugin.objects.all()[0].id)
            self.assertEqual(text_plugin_en.get_children().count(), 0)
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
            in_txt = u"""<img id="plugin_obj_%s" title="Link" alt="Link" src="/static/cms/img/icons/plugins/link.png">"""
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
            page_one_ph_one = page_one.placeholders.get(slot=u"col_sidebar")
            page_one_ph_two = page_one.placeholders.get(slot=u"col_left")
            page_one_ph_three = page_one.placeholders.get(slot=u"col_right")
            # verify the plugins got created
            org_placeholder_one_plugins = page_one_ph_one.get_plugins()
            self.assertEqual(len(org_placeholder_one_plugins), 1)
            org_placeholder_two_plugins = page_one_ph_two.get_plugins()
            self.assertEqual(len(org_placeholder_two_plugins), 2)
            org_placeholder_three_plugins = page_one_ph_three.get_plugins()
            self.assertEqual(len(org_placeholder_three_plugins), 0)
            self.assertEqual(page_one.placeholders.count(), 3)

            placeholder_count = Placeholder.objects.filter(page__publisher_is_draft=True).count()
            self.assertEqual(placeholder_count, 3)
            self.assertEqual(CMSPlugin.objects.count(), 3)
            # setup page_copy_target
            page_copy_target = create_page("Three Placeholder - page copy target", "col_three.html", "en",
                                           position="last-child", published=True, in_navigation=True)
            all_page_count = Page.objects.drafts().count()
            pre_copy_placeholder_count = Placeholder.objects.filter(page__publisher_is_draft=True).count()
            self.assertEqual(pre_copy_placeholder_count, 6)
            superuser = self.get_superuser()

            with force_language('en'):
                action_urls = text_plugin_two.get_action_urls()

            with self.login_user_context(superuser):
                # now move the parent text plugin to another placeholder
                post_data = {
                    'placeholder_id': page_one_ph_three.id,
                    'plugin_id': text_plugin_two.id,
                    'plugin_language': 'en',
                    'plugin_parent': '',

                }
                plugin_class = text_plugin_two.get_plugin_class_instance()
                expected = {
                    'reload': plugin_class.requires_reload(PLUGIN_MOVE_ACTION),
                    'urls': action_urls,
                }
                edit_url = URL_CMS_PLUGIN_PAGE_MOVE % page_one.id
                response = self.client.post(edit_url, post_data)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.content.decode('utf8')), expected)
                # check if the plugin got moved
                page_one = self.reload(page_one)
                self.reload(text_plugin_two)
                page_one_ph_one = page_one.placeholders.get(slot=u"col_sidebar")
                page_one_ph_two = page_one.placeholders.get(slot=u"col_left")
                page_one_ph_three = page_one.placeholders.get(slot=u"col_right")

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
            after_copy_page_count = Page.objects.drafts().count()
            after_copy_placeholder_count = Placeholder.objects.filter(page__publisher_is_draft=True).count()
            self.assertGreater(after_copy_page_count, all_page_count, u"no new page after copy")
            self.assertGreater(after_copy_page_plugin_count, post_add_plugin_count, u"plugin count is not grown")
            self.assertGreater(after_copy_placeholder_count, pre_copy_placeholder_count,
                               u"placeholder count is not grown")
            self.assertEqual(after_copy_page_count, 3, u"no new page after copy")
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
            page_two_ph_one = page_two.placeholders.get(slot=u"col_sidebar")
            page_two_ph_two = page_two.placeholders.get(slot=u"col_left")
            page_two_ph_three = page_two.placeholders.get(slot=u"col_right")
            # check if there are multiple pages assigned to this placeholders
            found_page = page_two_ph_one.page if page_two_ph_one else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_two.page if page_two_ph_two else None
            self.assertEqual(found_page, page_two)
            found_page = page_two_ph_three.page if page_two_ph_three else None
            self.assertEqual(found_page, page_two)
            # check the stored placeholders org vs copy
            msg = u'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_one.pk, page_one_ph_one.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_one.pk, page_one_ph_one.pk, msg)
            msg = u'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_two.pk, page_one_ph_two.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_two.pk, page_one_ph_two.pk, msg)
            msg = u'placehoder ids copy:%s org:%s copied page %s are identical - tree broken' % (
                page_two_ph_three.pk, page_one_ph_three.pk, page_two.pk)
            self.assertNotEquals(page_two_ph_three.pk, page_one_ph_three.pk, msg)
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
            msg = u"plugin count %s %s for placeholder one not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # placeholder 2
            count_plugins_copied = len(copied_placeholder_two_plugins)
            count_plugins_org = len(org_placeholder_two_plugins)
            msg = u"plugin count %s %s for placeholder two not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
            # placeholder 3
            count_plugins_copied = len(copied_placeholder_three_plugins)
            count_plugins_org = len(org_placeholder_three_plugins)
            msg = u"plugin count %s %s for placeholder three not equal" % (count_plugins_copied, count_plugins_org)
            self.assertEqual(count_plugins_copied, count_plugins_org, msg)
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
            self.assertNotEqual(org_link_child_plugin.id, copied_link_child_plugin.id, msg)
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
            self.assertNotEqual(org_placeholder.id, copied_placeholder.id, msg)

    def test_add_child_plugin(self):
        page_one = create_page(u"Three Placeholder", u"col_three.html", u"en",
                                   position=u"last-child", published=True, in_navigation=True)
        page_one_ph_one = page_one.placeholders.get(slot=u"col_sidebar")
        # add the text plugin to placeholder one
        text_plugin_en = add_plugin(page_one_ph_one, u"TextPlugin", u"en", body=u"Hello World")
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            post_data = {
                'name': 'test',
                'url': 'http://www.example.org/'
            }
            get_data = {
                'placeholder_id': page_one_ph_one.id,
                'plugin_type': 'LinkPlugin',
                'plugin_language': 'en',
                'plugin_parent': text_plugin_en.pk,

            }
            add_url = URL_CMS_PLUGIN_PAGE_ADD % page_one.pk + '?' + urlencode(
                get_data
            )
            response = self.client.post(add_url, post_data)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(
                response,
                'admin/cms/page/plugin/confirm_form.html'
            )
        link_plugin = CMSPlugin.objects.get(parent_id=text_plugin_en.pk)
        self.assertEqual(link_plugin.parent_id, text_plugin_en.pk)
        self.assertEqual(link_plugin.path, '00010001')
