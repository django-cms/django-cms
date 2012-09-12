# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import add_plugin, create_page
from cms.conf.global_settings import CMS_TEMPLATE_INHERITANCE_MAGIC
from cms.exceptions import DuplicatePlaceholderWarning
from cms.models.placeholdermodel import Placeholder
from cms.plugin_pool import plugin_pool
from cms.plugin_rendering import render_placeholder
from cms.plugins.link.cms_plugins import LinkPlugin
from cms.plugins.text.cms_plugins import TextPlugin
from cms.plugins.text.models import Text
from cms.test_utils.fixtures.fakemlng import FakemlngFixtures
from cms.test_utils.project.fakemlng.models import Translations
from cms.test_utils.project.placeholderapp.models import (Example1, Example2, 
    Example3, Example4, Example5)
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import (SettingsOverride, 
    UserLoginContext)
from cms.test_utils.util.mock import AttributeObject
from cms.utils.placeholder import PlaceholderNoAction, MLNGPlaceholderActions
from cms.utils.plugins import get_placeholders
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User, Permission
from django.contrib.messages.storage import default_storage
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponse
from django.template import TemplateSyntaxError, Template
from django.template.context import Context, RequestContext
from django.test import TestCase


class PlaceholderTestCase(CMSTestCase):
    def setUp(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        
        self._login_context = self.login_user_context(u)
        self._login_context.__enter__()
    
    def tearDown(self):
        self._login_context.__exit__(None, None, None)
        
    def test_placeholder_scanning_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_one.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'three']))
        
    def test_placeholder_scanning_include(self):
        placeholders = get_placeholders('placeholder_tests/test_two.html')
        self.assertEqual(sorted(placeholders), sorted([u'child', u'three']))
        
    def test_placeholder_scanning_double_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_three.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'new_three']))
        
    def test_placeholder_scanning_complex(self):
        placeholders = get_placeholders('placeholder_tests/test_four.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'child', u'four']))
        
    def test_placeholder_scanning_super(self):
        placeholders = get_placeholders('placeholder_tests/test_five.html')
        self.assertEqual(sorted(placeholders), sorted([u'one', u'extra_one', u'two', u'three']))
        
    def test_placeholder_scanning_nested(self):
        placeholders = get_placeholders('placeholder_tests/test_six.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'new_two', u'new_three']))
        
    def test_placeholder_scanning_duplicate(self):
        placeholders = self.assertWarns(DuplicatePlaceholderWarning, "Duplicate placeholder found: `one`", get_placeholders, 'placeholder_tests/test_seven.html')
        self.assertEqual(sorted(placeholders), sorted([u'one']))

    def test_placeholder_scanning_extend_outside_block(self):
        placeholders = get_placeholders('placeholder_tests/outside.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))

    def test_placeholder_scanning_extend_outside_block_nested(self):
        placeholders = get_placeholders('placeholder_tests/outside_nested.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))
    
    def test_fieldsets_requests(self):
        response = self.client.get(reverse('admin:placeholderapp_example1_add'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:placeholderapp_example2_add'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:placeholderapp_example3_add'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:placeholderapp_example4_add'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:placeholderapp_example5_add'))
        self.assertEqual(response.status_code, 200)
        
    def test_fieldsets(self):
        from cms.test_utils.project.placeholderapp import admin as __ # load admin
        request = self.get_request('/')
        admins = [
            (Example1, 2),
            (Example2, 3),
            (Example3, 3),
            (Example4, 3),
            (Example5, 4),
        ]
        for model, fscount in admins:
            ainstance = admin.site._registry[model]
            fieldsets = ainstance.get_fieldsets(request)
            form = ainstance.get_form(request, None)
            phfields = ainstance._get_placeholder_fields(form)
            self.assertEqual(len(fieldsets), fscount, (
                "Asserting fieldset count for %s. Got %s instead of %s: %s. "
                "Using %s." % (model.__name__, len(fieldsets),
                    fscount, fieldsets, ainstance.__class__.__name__)      
            ))
            for label, fieldset in fieldsets:
                fields = list(fieldset['fields'])
                for field in fields:
                    if field in phfields:
                        self.assertTrue(len(fields) == 1)
                        self.assertTrue('plugin-holder' in fieldset['classes'])
                        self.assertTrue('plugin-holder-nopage' in fieldset['classes'])
                        phfields.remove(field)
            self.assertEqual(phfields, [])
            
    def test_page_only_plugins(self):
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        response = self.client.get(reverse('admin:placeholderapp_example1_change', args=(ex.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'InheritPagePlaceholderPlugin')
        
    def test_inter_placeholder_plugin_move(self):
        ex = Example5(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        ph1 = ex.placeholder_1
        ph2 = ex.placeholder_2
        ph1_pl1 = add_plugin(ph1, TextPlugin, 'en', body='ph1 plugin1').cmsplugin_ptr
        ph1_pl2 = add_plugin(ph1, TextPlugin, 'en', body='ph1 plugin2').cmsplugin_ptr
        ph1_pl3 = add_plugin(ph1, TextPlugin, 'en', body='ph1 plugin3').cmsplugin_ptr
        ph2_pl1 = add_plugin(ph2, TextPlugin, 'en', body='ph2 plugin1').cmsplugin_ptr
        ph2_pl2 = add_plugin(ph2, TextPlugin, 'en', body='ph2 plugin2').cmsplugin_ptr
        ph2_pl3 = add_plugin(ph2, TextPlugin, 'en', body='ph2 plugin3').cmsplugin_ptr
        response = self.client.post(reverse('admin:placeholderapp_example5_move_plugin'), {
            'placeholder': ph2.slot,
            'placeholder_id': str(ph2.pk),
            'plugin_id': str(ph1_pl2.pk),
            'ids': "_".join([str(p.pk) for p in [ph2_pl1, ph1_pl2, ph2_pl2, ph2_pl3]])
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual([ph1_pl1, ph1_pl3], list(ph1.cmsplugin_set.order_by('position')))
        self.assertEqual([ph2_pl1, ph1_pl2, ph2_pl2, ph2_pl3], list(ph2.cmsplugin_set.order_by('position')))

    def test_nested_plugin_escapejs(self):
        """
        Checks #1366 error condition.
        When adding/editing a plugin whose icon_src() method returns a URL
        containing an hyphen, the hyphen is escaped by django escapejs resulting
        in a incorrect URL
        """
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            ex = Example1(
                char_1='one',
                char_2='two',
                char_3='tree',
                char_4='four'
            )
            ex.save()
            ph1 = ex.placeholder
            ###
            # add the test plugin
            ###
            test_plugin = add_plugin(ph1, u"EmptyPlugin", u"en")
            test_plugin.save()
            pl_url = "%sedit-plugin/%s/" % (
                reverse('admin:placeholderapp_example1_change', args=(ex.pk,)),
                test_plugin.pk)
            response = self.client.post(pl_url, {})
            self.assertContains(response,"/static/plugins/empty-image-file.png")

    def test_nested_plugin_escapejs_page(self):
        """
        Sibling test of the above, on a page.
        #1366 does not apply to placeholder defined in a page
        """
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            page = create_page('page', 'col_two.html', 'en')
            ph1 = page.placeholders.get(slot='col_left')
            ###
            # add the test plugin
            ###
            test_plugin = add_plugin(ph1, u"EmptyPlugin", u"en")
            test_plugin.save()
            pl_url = "%sedit-plugin/%s/" % (
                reverse('admin:cms_page_change', args=(page.pk,)),
                test_plugin.pk)
            response = self.client.post(pl_url, {})
            self.assertContains(response,"/static/plugins/empty-image-file.png")

    def test_placeholder_scanning_fail(self):
        self.assertRaises(TemplateSyntaxError, get_placeholders, 'placeholder_tests/test_eleven.html')

    def test_placeholder_tag(self):
        template = Template("{% load placeholder_tags %}{% render_placeholder placeholder %}")
        ctx = Context()
        self.assertEqual(template.render(ctx), "")
        request = self.get_request('/')
        rctx = RequestContext(request)
        self.assertEqual(template.render(rctx), "")
        placeholder = Placeholder.objects.create(slot="test")
        rctx['placeholder'] = placeholder
        self.assertEqual(template.render(rctx), "")
        self.assertEqual(placeholder.cmsplugin_set.count(), 0)
        add_plugin(placeholder, "TextPlugin", settings.LANGUAGES[0][0], body="test")
        self.assertEqual(placeholder.cmsplugin_set.count(), 1)
        rctx = RequestContext(request)
        placeholder = self.reload(placeholder)
        rctx['placeholder'] = placeholder
        self.assertEqual(template.render(rctx).strip(), "test")
    
    def test_placeholder_context_leaking(self):
        TEST_CONF = {'test': {'extra_context': {'width': 10}}}
        ph = Placeholder.objects.create(slot='test')
        class NoPushPopContext(Context):
            def push(self):
                pass
            pop = push
        context = NoPushPopContext()
        context['request'] = self.get_request()
        with SettingsOverride(CMS_PLACEHOLDER_CONF=TEST_CONF):
            render_placeholder(ph, context)
            self.assertTrue('width' in context)
            self.assertEqual(context['width'], 10)
            ph.render(context, None)
            self.assertTrue('width' in context)
            self.assertEqual(context['width'], 10)

    def test_placeholder_scanning_nested_super(self):
        placeholders = get_placeholders('placeholder_tests/nested_super_level1.html')
        self.assertEqual(sorted(placeholders), sorted([u'level1', u'level2', u'level3', u'level4']))


class PlaceholderActionTests(FakemlngFixtures, CMSTestCase):
    
    def test_placeholder_no_action(self):
        actions = PlaceholderNoAction()
        self.assertEqual(actions.get_copy_languages(), [])
        self.assertFalse(actions.copy())
        
    def test_mlng_placeholder_actions_get_copy_languages(self):
        actions = MLNGPlaceholderActions()
        fr = Translations.objects.get(language_code='fr')
        de = Translations.objects.get(language_code='de')
        en = Translations.objects.get(language_code='en')
        fieldname = 'placeholder'
        fr_copy_languages = actions.get_copy_languages(
            fr.placeholder, Translations, fieldname
        )
        de_copy_languages = actions.get_copy_languages(
            de.placeholder, Translations, fieldname
        )
        en_copy_languages = actions.get_copy_languages(
            en.placeholder, Translations, fieldname
        )
        EN = ('en', 'English')
        FR = ('fr', 'French')
        self.assertEqual(fr_copy_languages, [EN])
        self.assertEqual(de_copy_languages, [EN, FR])
        self.assertEqual(en_copy_languages, [FR])
        
    def test_mlng_placeholder_actions_copy(self):
        actions = MLNGPlaceholderActions()
        fr = Translations.objects.get(language_code='fr')
        de = Translations.objects.get(language_code='de')
        self.assertEqual(fr.placeholder.cmsplugin_set.count(), 1)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 0)
        
        new_plugins = actions.copy(de.placeholder, 'fr', 'placeholder', Translations, 'de')
        self.assertEqual(len(new_plugins), 1)
        
        de = self.reload(de)
        fr = self.reload(fr)
        
        self.assertEqual(fr.placeholder.cmsplugin_set.count(), 1)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 1)
        
    def test_mlng_placeholder_actions_empty_copy(self):
        actions = MLNGPlaceholderActions()
        fr = Translations.objects.get(language_code='fr')
        de = Translations.objects.get(language_code='de')
        self.assertEqual(fr.placeholder.cmsplugin_set.count(), 1)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 0)
        
        new_plugins = actions.copy(fr.placeholder, 'de', 'placeholder', Translations, 'fr')
        self.assertEqual(len(new_plugins), 0)

        de = self.reload(de)
        fr = self.reload(fr)
        
        self.assertEqual(fr.placeholder.cmsplugin_set.count(), 1)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 0)
        
    def test_mlng_placeholder_actions_no_placeholder(self):
        actions = MLNGPlaceholderActions()
        Translations.objects.filter(language_code='nl').update(placeholder=None)
        de = Translations.objects.get(language_code='de')
        nl = Translations.objects.get(language_code='nl')
        self.assertEqual(nl.placeholder, None)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 0)
        
        okay = actions.copy(de.placeholder, 'nl', 'placeholder', Translations, 'de')
        self.assertEqual(okay, False)
        
        de = self.reload(de)
        nl = self.reload(nl)
        
        nl = Translations.objects.get(language_code='nl')
        de = Translations.objects.get(language_code='de')
        
class PlaceholderModelTests(CMSTestCase):
    def get_mock_user(self, superuser):
        return AttributeObject(
            is_superuser=superuser,
            has_perm=lambda string: False,
        ) 
    
    def get_mock_request(self, superuser=True):
        return AttributeObject(
            superuser=superuser,
            user=self.get_mock_user(superuser)
        )
    
    def test_check_placeholder_permissions_ok_for_superuser(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph.has_change_permission(self.get_mock_request(True))
        self.assertTrue(result)
        
    def test_check_placeholder_permissions_nok_for_user(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph.has_change_permission(self.get_mock_request(False))
        self.assertFalse(result)
    
    def test_check_unicode_rendering(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = unicode(ph)
        self.assertEqual(result,u'test')
    
    def test_excercise_get_attached_model(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph._get_attached_model()
        self.assertEqual(result, None) # Simple PH - no model
        
    def test_excercise_get_attached_field_name(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph._get_attached_field_name()
        self.assertEqual(result, None) # Simple PH - no field name
    
    def test_excercise_get_attached_models_notplugins(self):
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        ph = ex.placeholder
        result = list(ph._get_attached_models())
        self.assertEqual(result, [Example1]) # Simple PH - Example1 model
        add_plugin(ph, TextPlugin, 'en', body='en body')
        result = list(ph._get_attached_models())
        self.assertEqual(result, [Example1]) # Simple PH still one Example1 model
        
    def test_excercise_get_attached_fields_notplugins(self):
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four',
        )
        ex.save()
        ph = ex.placeholder
        result = [f.name for f in list(ph._get_attached_fields())]
        self.assertEqual(result, ['placeholder']) # Simple PH - placeholder field name
        add_plugin(ph, TextPlugin, 'en', body='en body')
        result = [f.name for f in list(ph._get_attached_fields())]
        self.assertEqual(result, ['placeholder']) # Simple PH - still one placeholder field name
        
class PlaceholderAdminTest(CMSTestCase):
    placeholderconf = {'test': {
            'limits': {
                'global': 2,
                'TextPlugin': 1,
            }
        }
    }
    def get_placeholder(self):
        return Placeholder.objects.create(slot='test')
    
    def get_admin(self):
        admin.autodiscover()
        return admin.site._registry[Example1]
    
    def get_post_request(self, data):
        return self.get_request(post_data=data)
    
    def test_global_limit(self):
        placeholder = self.get_placeholder()
        admin = self.get_admin()
        data = {
            'plugin_type': 'LinkPlugin',
            'placeholder': placeholder.pk,
            'language': 'en',
        }
        superuser = self.get_superuser()
        with UserLoginContext(self, superuser):
            with SettingsOverride(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request(data)
                response = admin.add_plugin(request) # first
                self.assertEqual(response.status_code, 200)
                response = admin.add_plugin(request) # second
                self.assertEqual(response.status_code, 200)
                response = admin.add_plugin(request) # third
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content, "This placeholder already has the maximum number of plugins.")

    def test_type_limit(self):
        placeholder = self.get_placeholder()
        admin = self.get_admin()
        data = {
            'plugin_type': 'TextPlugin',
            'placeholder': placeholder.pk,
            'language': 'en',
        }
        superuser = self.get_superuser()
        with UserLoginContext(self, superuser):
            with SettingsOverride(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                request = self.get_post_request(data)
                response = admin.add_plugin(request) # first
                self.assertEqual(response.status_code, 200)
                response = admin.add_plugin(request) # second
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content, "This placeholder already has the maximum number (1) of TextPlugin plugins.")


class PlaceholderPluginPermissionTests(PlaceholderAdminTest):

    def _testuser(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = False)
        u.set_password("test")
        u.save()
        return u

    def _create_example(self):
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        self._placeholder = ex.placeholder

    def _create_plugin(self):
        self._plugin = add_plugin(self._placeholder, 'TextPlugin', 'en')

    def _give_permission(self, user, model, permission_type, save=True):
        codename = '%s_%s' % (permission_type, model._meta.object_name.lower())
        user.user_permissions.add(Permission.objects.get(codename=codename))

    def _delete_permission(self, user, model, permission_type, save=True):
        codename = '%s_%s' % (permission_type, model._meta.object_name.lower())
        user.user_permissions.remove(Permission.objects.get(codename=codename))

    def _post_request(self, user):
        data = {
            'plugin_type': 'TextPlugin',
            'placeholder': self._placeholder.pk,
            'language': 'en',
        }
        request = self.get_post_request(data)
        request.user = self.reload(user)
        request._messages = default_storage(request)
        return request

    def test_plugin_add_requires_permissions(self):
        """User wants to add a plugin to the example app placeholder but has no permissions"""
        self._create_example()
        normal_guy = self._testuser()
        admin = self.get_admin()
        request = self._post_request(normal_guy)
        response = admin.add_plugin(request)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        # The user gets the permission only for the plugin
        self._give_permission(normal_guy, Text, 'add')
        request = self._post_request(normal_guy)
        response = admin.add_plugin(request)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        # the user gets the permission only for the app
        self._delete_permission(normal_guy, Text, 'add')
        self._give_permission(normal_guy, Example1, 'add')
        request = self._post_request(normal_guy)
        response = admin.add_plugin(request)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        # user gets permissions for the plugin and the app
        self._give_permission(normal_guy, Text, 'add')
        request = self._post_request(normal_guy)
        response = admin.add_plugin(request)
        self.assertEqual(response.status_code, HttpResponse.status_code)


    def test_plugin_edit_requires_permissions(self):
        """User wants to edit a plugin to the example app placeholder but has no permissions"""
        self._create_example()
        self._create_plugin()
        normal_guy = self._testuser()
        admin = self.get_admin()
        request = self._post_request(normal_guy)
        response = admin.edit_plugin(request, self._plugin.id)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        # The user gets the permission only for the plugin
        self._give_permission(normal_guy, Text, 'change')
        request = self._post_request(normal_guy)
        response = admin.edit_plugin(request, self._plugin.id)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        # the user gets the permission only for the app
        self._delete_permission(normal_guy, Text, 'change')
        self._give_permission(normal_guy, Example1, 'change')
        request = self._post_request(normal_guy)
        response = admin.edit_plugin(request, self._plugin.id)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        # user gets permissions for the plugin and the app
        self._give_permission(normal_guy, Text, 'change')
        request = self._post_request(normal_guy)
        response = admin.edit_plugin(request, self._plugin.id)
        # It looks like it breaks here because of a missing csrf token in the request
        # I have no idea how to fix this
        self.assertEqual(response.status_code, HttpResponse.status_code, response)


class PlaceholderConfTests(TestCase):
    def test_get_all_plugins_single_page(self):
        page = create_page('page', 'col_two.html', 'en')
        placeholder = page.placeholders.get(slot='col_left')
        conf = {
            'col_two': {
                'plugins': ['TextPlugin', 'LinkPlugin'],
            },
            'col_two.html col_left': {
                'plugins': ['LinkPlugin'],
            },
        }
        with SettingsOverride(CMS_PLACEHOLDER_CONF=conf):
            plugins = plugin_pool.get_all_plugins(placeholder, page)
            self.assertEqual(len(plugins), 1, plugins)
            self.assertEqual(plugins[0], LinkPlugin)

    def test_get_all_plugins_inherit(self):
        parent = create_page('parent', 'col_two.html', 'en')
        page = create_page('page', CMS_TEMPLATE_INHERITANCE_MAGIC, 'en', parent=parent)
        placeholder = page.placeholders.get(slot='col_left')
        conf = {
            'col_two': {
                'plugins': ['TextPlugin', 'LinkPlugin'],
            },
            'col_two.html col_left': {
                'plugins': ['LinkPlugin'],
            },
        }
        with SettingsOverride(CMS_PLACEHOLDER_CONF=conf):
            plugins = plugin_pool.get_all_plugins(placeholder, page)
            self.assertEqual(len(plugins), 1, plugins)
            self.assertEqual(plugins[0], LinkPlugin)
