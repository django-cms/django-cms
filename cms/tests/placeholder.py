# -*- coding: utf-8 -*-
from cms.exceptions import DuplicatePlaceholderWarning
from cms.models.placeholdermodel import Placeholder
from cms.test.testcases import CMSTestCase
from cms.utils.placeholder import PlaceholderNoAction, MLNGPlaceholderActions
from cms.utils.plugins import get_placeholders
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template import TemplateSyntaxError, Template
from django.template.context import Context, RequestContext
from cms.test.apps.fakemlng.models import Translations
from cms.test.apps.placeholderapp.models import Example1, Example2, Example3, Example4, \
    Example5


class PlaceholderTestCase(CMSTestCase):
    def setUp(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        
        self.login_user(u)
        
    def test_01_placeholder_scanning_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_one.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'three']))
        
    def test_02_placeholder_scanning_include(self):
        placeholders = get_placeholders('placeholder_tests/test_two.html')
        self.assertEqual(sorted(placeholders), sorted([u'child', u'three']))
        
    def test_03_placeholder_scanning_double_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_three.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'new_three']))
        
    def test_04_placeholder_scanning_complex(self):
        placeholders = get_placeholders('placeholder_tests/test_four.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'child', u'four']))
        
    def test_05_placeholder_scanning_super(self):
        placeholders = get_placeholders('placeholder_tests/test_five.html')
        self.assertEqual(sorted(placeholders), sorted([u'one', u'extra_one', u'two', u'three']))
        
    def test_06_placeholder_scanning_nested(self):
        placeholders = get_placeholders('placeholder_tests/test_six.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'new_two', u'new_three']))
        
    def test_07_placeholder_scanning_duplicate(self):
        placeholders = self.assertWarns(DuplicatePlaceholderWarning, "Duplicate placeholder found: `one`", get_placeholders, 'placeholder_tests/test_seven.html')
        self.assertEqual(sorted(placeholders), sorted([u'one']))

    def test_08_placeholder_scanning_extend_outside_block(self):
        placeholders = get_placeholders('placeholder_tests/outside.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))
    
    def test_09_fieldsets_requests(self):
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
        
    def test_10_fieldsets(self):
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

    def test_11_placeholder_scanning_fail(self):
        self.assertRaises(TemplateSyntaxError, get_placeholders, 'placeholder_tests/test_eleven.html')

    def test_12_placeholder_tag(self):
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
        self.add_plugin(placeholder=placeholder, body="test", language=settings.LANGUAGES[0][0])
        self.assertEqual(placeholder.cmsplugin_set.count(), 1)
        rctx = RequestContext(request)
        placeholder = self.reload(placeholder)
        rctx['placeholder'] = placeholder
        self.assertEqual(template.render(rctx).strip(), "test")


class PlaceholderActionTests(CMSTestCase):
    fixtures = ['fakemlng.json']
    
    def test_01_placeholder_no_action(self):
        actions = PlaceholderNoAction()
        self.assertEqual(actions.get_copy_languages(), [])
        self.assertFalse(actions.copy())
        
    def test_02_mlng_placeholder_actions_get_copy_languages(self):
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
        
    def test_03_mlng_placeholder_actions_copy(self):
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
        
    def test_04_mlng_placeholder_actions_empty_copy(self):
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
        
    def test_05_mlng_placeholder_actions_no_placeholder(self):
        actions = MLNGPlaceholderActions()
        nl = Translations.objects.get(language_code='nl')
        de = Translations.objects.get(language_code='de')
        self.assertEqual(nl.placeholder, None)
        self.assertEqual(de.placeholder.cmsplugin_set.count(), 0)
        
        okay = actions.copy(de.placeholder, 'nl', 'placeholder', Translations, 'de')
        self.assertEqual(okay, False)
        
        de = self.reload(de)
        nl = self.reload(nl)
        
        nl = Translations.objects.get(language_code='nl')
        de = Translations.objects.get(language_code='de')
        
class PlaceholderModelTests(CMSTestCase):
    
    class MockUser():
        def __init__(self,superuser=True):
            self.is_superuser = superuser
        def has_perm(self, string):
            return False # always return false, for simplicity 
    
    class MockRequest():
        def __init__(self, superuser=True):
            self.superuser = superuser
            self.user = PlaceholderModelTests.MockUser(self.superuser)
    
    def test_01_check_placeholder_permissions_ok_for_superuser(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph.has_change_permission(self.MockRequest())
        self.assertTrue(result)
        
    def test_02_check_placeholder_permissions_nok_for_user(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph.has_change_permission(self.MockRequest(False))
        self.assertFalse(result)
    
    def test_03_check_unicode_rendering(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = unicode(ph)
        self.assertEqual(result,u'test')
    
    def test_04_excercise_get_attached_model(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph._get_attached_model()
        self.assertEqual(result, None) # Simple PH - no model
        
    def test_05_excercise_get_attached_field_name(self):
        ph = Placeholder.objects.create(slot='test', default_width=300)
        result = ph._get_attached_field_name()
        self.assertEqual(result, None) # Simple PH - no field name
