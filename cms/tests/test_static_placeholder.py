# -*- coding: utf-8 -*-
from __future__ import with_statement
import json

from django.contrib.admin.sites import site
from django.template import Context
from django.template.base import Template
from django.utils.encoding import force_text

from cms.api import add_plugin
from cms.constants import PLUGIN_MOVE_ACTION, PLUGIN_COPY_ACTION
from cms.models import StaticPlaceholder, Placeholder, CMSPlugin
from cms.tests.test_plugins import PluginsTestBaseCase
from cms.utils.i18n import force_language
from cms.utils.urlutils import admin_reverse


class StaticPlaceholderTestCase(PluginsTestBaseCase):
    @property
    def admin_class(self):
        return site._registry[StaticPlaceholder]

    def fill_placeholder(self, placeholder=None):
        if placeholder is None:
            placeholder = Placeholder(slot=u"some_slot")
            placeholder.save()  # a good idea, if not strictly necessary


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

    def get_admin(self):
        usr = self._create_user("admin", True, True)
        return usr

    def test_template_creation(self):
        self.assertObjectDoesNotExist(StaticPlaceholder.objects.all(), code='foobar')
        self.assertObjectDoesNotExist(Placeholder.objects.all(), slot='foobar')
        t = Template('{% load cms_tags %}{% static_placeholder "foobar" %}')
        t.render(self.get_context('/'))
        self.assertObjectExist(StaticPlaceholder.objects.all(), code='foobar',
                               creation_method=StaticPlaceholder.CREATION_BY_TEMPLATE)
        self.assertEqual(Placeholder.objects.filter(slot='foobar').count(), 2)

    def test_empty(self):
        self.assertObjectDoesNotExist(StaticPlaceholder.objects.all(), code='foobar')
        self.assertObjectDoesNotExist(Placeholder.objects.all(), slot='foobar')
        t = Template('{% load cms_tags %}{% static_placeholder "foobar" or %}No Content{% endstatic_placeholder %}')
        rendered = t.render(self.get_context('/'))
        self.assertIn("No Content", rendered)

        t = Template('{% load cms_tags %}{% static_placeholder "" %}')
        rendered = t.render(self.get_context('/'))
        self.assertEqual("", rendered)

        t = Template('{% load cms_tags %}{% static_placeholder code or %}No Content{% endstatic_placeholder %}')
        rendered = t.render(Context({'code': StaticPlaceholder.objects.all()[0]}))
        self.assertIn("No Content", rendered)

        for p in Placeholder.objects.all():
            add_plugin(p, 'TextPlugin', 'en', body='test')
        t = Template('{% load cms_tags %}{% static_placeholder "foobar" or %}No Content{% endstatic_placeholder %}')
        rendered = t.render(self.get_context('/'))
        self.assertNotIn("No Content", rendered)
        self.assertEqual(StaticPlaceholder.objects.filter(site_id__isnull=True, code='foobar').count(), 1)

    def test_local(self):
        self.assertObjectDoesNotExist(StaticPlaceholder.objects.all(), code='foobar')
        self.assertObjectDoesNotExist(Placeholder.objects.all(), slot='foobar')
        t = Template('{% load cms_tags %}{% static_placeholder "foobar" site or %}No Content{% endstatic_placeholder %}')
        rendered = t.render(self.get_context('/'))
        self.assertIn("No Content", rendered)
        for p in Placeholder.objects.all():
            add_plugin(p, 'TextPlugin', 'en', body='test')
        rendered = t.render(self.get_context('/'))
        self.assertNotIn("No Content", rendered)
        self.assertEqual(StaticPlaceholder.objects.filter(site_id__isnull=False, code='foobar').count(), 1)

    def test_publish_stack(self):
        static_placeholder = StaticPlaceholder.objects.create(name='foo', code='bar', site_id=1)
        self.fill_placeholder(static_placeholder.draft)
        static_placeholder.dirty = True
        static_placeholder.save()
        self.assertEqual(static_placeholder.draft.cmsplugin_set.all().count(), 2)
        self.assertEqual(static_placeholder.public.cmsplugin_set.all().count(), 0)
        with self.login_user_context(self.get_superuser()):
            response = self.client.post('%s?statics=%s' % (admin_reverse("cms_page_publish_page", args=[1, 'en']), static_placeholder.pk))
            self.assertEqual(response.status_code, 302)

    def test_permissions(self):
        static_placeholder = StaticPlaceholder.objects.create(name='foo', code='bar', site_id=1)
        request = self.get_request()

        request.user = self._create_user('user_a', is_staff=True, is_superuser=False, permissions=['change_staticplaceholder'])
        self.assertTrue( static_placeholder.has_change_permission(request) )
        self.assertFalse( static_placeholder.has_publish_permission(request) )

        request.user = self._create_user('user_b', is_staff=True, is_superuser=False, permissions=['change_staticplaceholder', 'publish_page'])
        self.assertTrue( static_placeholder.has_change_permission(request) )
        self.assertTrue( static_placeholder.has_publish_permission(request) )

        request.user = self.get_superuser()
        self.assertTrue( static_placeholder.has_change_permission(request) )
        self.assertTrue( static_placeholder.has_publish_permission(request) )

    def test_move_plugin(self):
        static_placeholder_source = StaticPlaceholder.objects.create(name='foobar', code='foobar', site_id=1)
        static_placeholder_target = StaticPlaceholder.objects.create(name='foofoo', code='foofoo', site_id=1)
        sourceplugin = add_plugin(static_placeholder_source.draft, 'TextPlugin', 'en', body='test')
        plugin_class = sourceplugin.get_plugin_class_instance()

        with force_language('en'):
            action_urls = sourceplugin.get_action_urls()

        expected = {
            'reload': plugin_class.requires_reload(PLUGIN_MOVE_ACTION),
            'urls': action_urls,
        }
        admin = self.get_admin()

        with self.login_user_context(admin):
            request = self.get_request(post_data={'plugin_id': sourceplugin.pk,
                'placeholder_id': static_placeholder_target.draft.id,
                'plugin_parent': '', 'plugin_language': 'en'})
            response = self.admin_class.move_plugin(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.content.decode('utf8')), expected)
            source = StaticPlaceholder.objects.get(pk=static_placeholder_source.pk)
            target = StaticPlaceholder.objects.get(pk=static_placeholder_target.pk)
            self.assertTrue(source.dirty)
            self.assertTrue(target.dirty)

    def test_copy_plugin(self):
        static_placeholder_source = StaticPlaceholder.objects.create(name='foobar', code='foobar', site_id=1)
        static_placeholder_target = StaticPlaceholder.objects.create(name='foofoo', code='foofoo', site_id=1)
        sourceplugin = add_plugin(static_placeholder_source.draft, 'TextPlugin', 'en', body='test source')
        targetplugin = add_plugin(static_placeholder_target.draft, 'TextPlugin', 'en', body='test dest')
        StaticPlaceholder.objects.filter(pk=static_placeholder_source.pk).update(dirty=False)
        plugin_class = sourceplugin.get_plugin_class_instance()
        admin = self.get_admin()

        with self.login_user_context(admin):
            request = self.get_request(post_data={
                'source_language': 'en',
                'source_placeholder_id': static_placeholder_source.draft.pk,
                'source_plugin_id': sourceplugin.pk,
                'target_language': 'en',
                'target_placeholder_id': static_placeholder_target.draft.pk,
                'target_plugin_id': targetplugin.pk,
            })
            response = self.admin_class.copy_plugins(request)

            # generate the expected response
            plugin_list = CMSPlugin.objects.filter(
                language='en', placeholder_id=static_placeholder_target.draft.pk).order_by(
                'depth', 'position')
            reduced_list = []
            for plugin in plugin_list:
                reduced_list.append(
                    {
                        'id': plugin.pk, 'type': plugin.plugin_type, 'parent': plugin.parent_id,
                        'position': plugin.position, 'desc': force_text(plugin.get_short_description()),
                        'language': plugin.language, 'placeholder_id': static_placeholder_target.draft.pk
                    }
                )
            expected = json.loads(
                json.dumps({'plugin_list': reduced_list, 'reload': plugin_class.requires_reload(PLUGIN_COPY_ACTION)}))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.content.decode('utf8')), expected)

            # Check dirty bit
            source = StaticPlaceholder.objects.get(pk=static_placeholder_source.pk)
            target = StaticPlaceholder.objects.get(pk=static_placeholder_target.pk)
            self.assertFalse(source.dirty)
            self.assertTrue(target.dirty)

    def test_create_by_admin(self):
        url = admin_reverse("cms_staticplaceholder_add")
        with self.login_user_context(self.get_superuser()):
            response = self.client.post(url, data={'name': 'Name', 'code': 'content'})
            self.assertEqual(response.status_code, 302)
