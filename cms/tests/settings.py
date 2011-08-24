# -*- coding: utf-8 -*-
from __future__ import with_statement
from django.core.exceptions import ImproperlyConfigured
from cms.conf.patch import post_patch, post_patch_check
from cms.conf.global_settings import CMS_TEMPLATE_INHERITANCE_MAGIC
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.testcases import CMSTestCase

class SettingsTests(CMSTestCase):
    def test_cms_templates_length(self):
        '''
        Ensure that the correct exception is raised when CMS_TEMPLATES is
        configured with an empty tuple or the magic value 'INHERIT'
        '''
        improperly_configured_template_tests = (
            # don't allow 0 length
            (),

            # don't allow length of 1 if the only value is the magic inheritance
            ((CMS_TEMPLATE_INHERITANCE_MAGIC, None),),
        )
        for value_to_test in improperly_configured_template_tests:
            with SettingsOverride(DEBUG=True, CMS_TEMPLATES=value_to_test):
                self.assertRaises(ImproperlyConfigured, post_patch_check)

    def test_cms_templates_none(self):
        '''
        In fixing #814, CMS_TEMPLATES default after patching changes from None
        to an empty tuple. As such, If the user has decided to set None for some
        reason, this test lets us know what to expect.
        As it stands, we should get a TypeError because post_patch attempts to
        turn None into a tuple explicitly.
        '''

        # with CMS_TEMPLATE_INHERITANCE we step into an if statement that errors
        with SettingsOverride(DEBUG=True, CMS_TEMPLATE_INHERITANCE=True, CMS_TEMPLATES=None):
            self.assertRaises(TypeError, post_patch)

        # without CMS_TEMPLATE_INHERITANCE enabled, the function should return nothing
        with SettingsOverride(DEBUG=True, CMS_TEMPLATE_INHERITANCE=False, CMS_TEMPLATES=None):
            self.assertEqual(None, post_patch())

    def test_cms_templates_valid(self):
        '''
        These are all formats that should be valid, thus return nothing when DEBUG is True.
        '''
        success_template_tests = (
            # one valid template
            (('col_two.html', 'two columns'),),

            # two valid templates
            (('col_two.html', 'two columns'),
             ('col_three.html', 'three columns'),),

            # three valid templates
            (('col_two.html', 'two columns'),
             ('col_three.html', 'three columns'),
             ('nav_playground.html', 'navigation examples'),),

            # three valid templates + inheritance
            (('col_two.html', 'two columns'),
             ('col_three.html', 'three columns'),
             ('nav_playground.html', 'navigation examples'),
             (CMS_TEMPLATE_INHERITANCE_MAGIC, None),),

            # same valid templates as above, ensuring we don't short circuit when inheritance
            # magic comes first.
            ((CMS_TEMPLATE_INHERITANCE_MAGIC, None),
             ('col_two.html', 'two columns'),
             ('col_three.html', 'three columns'),
             ('nav_playground.html', 'navigation examples'),),
        )
        for value_to_test in success_template_tests:
            with SettingsOverride(DEBUG=True, CMS_TEMPLATES=value_to_test):
                self.assertEqual(None, post_patch_check())
