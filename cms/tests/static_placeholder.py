# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.models import StaticPlaceholder
from django.template.base import Template
from cms.api import add_plugin
from cms.models.placeholdermodel import Placeholder
from cms.stacks.models import Stack
from cms.tests.plugins import PluginsTestBaseCase


URL_CMS_MOVE_PLUGIN = u'/en/admin/cms/page/%d/move-plugin/'


class StaticPlaceholderTestCase(PluginsTestBaseCase):
    def fill_placeholder(self, placeholder=None):
        if placeholder is None:
            placeholder = Placeholder(slot=u"some_slot")
            placeholder.save() # a good idea, if not strictly necessary


        # plugin in placeholder
        plugin_1 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"01",
        )
        plugin_1.save()

        # IMPORTANT: plugins must be reloaded, before they can be assigned
        # as a parent. Otherwise, the MPTT structure doesn't seem to rebuild
        # properly.

        # child of plugin_1
        plugin_2 = add_plugin(placeholder, u"TextPlugin", u"en",
                              body=u"02",
        )
        plugin_1 = self.reload(plugin_1)
        plugin_2.parent = plugin_1
        plugin_2.save()
        return placeholder

    def test_template_creation(self):
        self.assertObjectDoesNotExist(Stack.objects.all(), code='foobar')
        self.assertObjectDoesNotExist(Placeholder.objects.all(), slot='foobar')
        t = Template('{% load cms_tags %}{% static_placeholder "foobar" %}')
        t.render(self.get_context('/'))
        self.assertObjectExist(StaticPlaceholder.objects.all(), code='foobar', creation_method=StaticPlaceholder.CREATION_BY_TEMPLATE)
        self.assertEqual(Placeholder.objects.filter(slot='foobar').count(), 2)

    def test_publish_stack(self):
        static_placeholder = StaticPlaceholder.objects.create(name='foo', code='bar')
        self.fill_placeholder(static_placeholder.draft)
        static_placeholder.dirty = True
        static_placeholder.save()
        self.assertEqual(static_placeholder.draft.cmsplugin_set.all().count(), 2)
        self.assertEqual(static_placeholder.public.cmsplugin_set.all().count(), 0)
        request = self.get_request()
        static_placeholder.publish(request)