# -*- coding: utf-8 -*-
import unittest
import doctest
from django.conf import settings


# doc testing in some modules
from cms.utils import urlutils
from cms.tests.page import PagesTestCase
from cms.tests.permmod import PermissionModeratorTestCase
from cms.tests.site import SiteTestCase
from cms.tests.navextender import NavExtenderTestCase
from cms.tests.plugins import PluginsTestCase
from cms.tests.reversion_tests import ReversionTestCase
from cms.tests.menu import MenusTestCase

settings.CMS_PERMISSION = True
settings.CMS_MODERATOR = True
settings.CMS_NAVIGATION_EXTENDERS = (
    ('example.categories.navigation.get_nodes', 'Categories'),
    ('example.sampleapp.menu_extender.get_nodes', 'SampleApp Menu'),
)

settings.CMS_FLAT_URLS = False
settings.CMS_MENU_TITLE_OVERWRITE = True
settings.CMS_HIDE_UNTRANSLATED = False
settings.CMS_URL_OVERWRITE = True
if not "example.sampleapp" in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ["example.sampleapp"]

def suite():
    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(urlutils))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PagesTestCase))
    
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(SiteTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(NavExtenderTestCase))
    if "cms.plugins.text" in settings.INSTALLED_APPS:
        s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PluginsTestCase))
        if "reversion" in settings.INSTALLED_APPS:
            s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(ReversionTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PermissionModeratorTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(MenusTestCase))
    
    return s
 
def test_runner_with_coverage(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    """Custom test runner.  Follows the django.test.simple.run_tests() interface."""
    import os, shutil, sys
 
    # Look for coverage.py in __file__/lib as well as sys.path
    sys.path = [os.path.join(os.path.dirname(__file__), "lib")] + sys.path
     
    import coverage
    from django.test.simple import run_tests as django_test_runner
     
    from django.conf import settings
    
    # Start code coverage before anything else if necessary
    #if hasattr(settings, 'COVERAGE_MODULES') and not test_labels:
    coverage.use_cache(0) # Do not cache any of the coverage.py stuff
    coverage.start()
 
    test_results = django_test_runner(test_labels, verbosity, interactive, extra_tests)
 
    # Stop code coverage after tests have completed
    #if hasattr(settings, 'COVERAGE_MODULES') and not test_labels:
    coverage.stop()
 
    # Print code metrics header
    print ''
    print '----------------------------------------------------------------------'
    print ' Unit Test Code Coverage Results'
    print '----------------------------------------------------------------------'
    
    # Report code coverage metrics
    coverage_modules = []
    if hasattr(settings, 'COVERAGE_MODULES') and (not test_labels or 'cms' in test_labels):
        for module in settings.COVERAGE_MODULES:
            coverage_modules.append(__import__(module, globals(), locals(), ['']))
    coverage.report(coverage_modules, show_missing=1)
            #Print code metrics footer
    print '----------------------------------------------------------------------'

    return test_results