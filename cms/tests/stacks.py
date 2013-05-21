# -*- coding: utf-8 -*-
from __future__ import with_statement
from django.template.base import Template
from django.core.urlresolvers import reverse
from cms.api import add_plugin
from cms.models.placeholdermodel import Placeholder
from cms.stacks.forms import StackInsertionForm
from cms.stacks.models import Stack, StackLink
from cms.tests.plugins import PluginsTestBaseCase


URL_CMS_MOVE_PLUGIN = u'/en/admin/cms/page/%d/move-plugin/'


class StacksTestCase(PluginsTestBaseCase):
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
        t = Template('{% load stack_tags %}{% stack "foobar" %}')
        t.render(self.get_context('/'))
        self.assertObjectExist(Stack.objects.all(), code='foobar', creation_method=Stack.CREATION_BY_TEMPLATE)

    def test_create_stack_from_placeholder(self):
        placeholder = self.fill_placeholder()
        response = self.client.post(reverse('admin:stacks_stack_create_stack', kwargs={'placeholder_id': placeholder.pk}), data={'name': 'foo', 'code': 'bar'})
        new_placeholder = Placeholder.objects.get(stacks_contents__code='bar')
        self.assertEqual(len(placeholder.get_plugins()), len(new_placeholder.get_plugins()))

    def test_create_stack_from_plugin(self):
        placeholder = self.fill_placeholder()
        plugin = placeholder.get_plugins().filter(parent=None).get()
        response = self.client.post(reverse('admin:stacks_stack_create_stack_from_plugin', kwargs={'placeholder_id': placeholder.pk, 'plugin_id': plugin.pk}), data={'name': 'foo', 'code': 'bar'})
        new_placeholder = Placeholder.objects.get(stacks_contents__code='bar')
        self.assertEqual(len(placeholder.get_plugins()), len(new_placeholder.get_plugins()))

    def test_insert_stack_plugin(self):
        placeholder = self.fill_placeholder()
        stack = Stack.objects.create(name='foo', code='bar')
        self.fill_placeholder(stack.content)
        new_placeholder = Placeholder.objects.create(slot='some_other_slot')
        response = self.client.post(reverse('admin:stacks_stack_insert_stack', kwargs={'placeholder_id': new_placeholder.pk}), data={'insertion_type': StackInsertionForm.INSERT_LINK, 'stack': stack.pk, 'language_code': 'en'})
        self.assertEquals(len(new_placeholder.get_plugins()), 1)
        self.assertEquals(len(StackLink.objects.get(placeholder=new_placeholder).stack.content.get_plugins()), len(placeholder.get_plugins()))
        another_new_placeholder = Placeholder.objects.create(slot='some_other_slot')
        response = self.client.post(reverse('admin:stacks_stack_insert_stack', kwargs={'placeholder_id': another_new_placeholder.pk}), data={'insertion_type': StackInsertionForm.INSERT_COPY, 'stack': stack.pk, 'language_code': 'en'})
        self.assertEquals(len(stack.content.get_plugins()), len(another_new_placeholder.get_plugins()))
