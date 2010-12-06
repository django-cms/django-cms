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
from cms.tests.nonroot import NonRootCase

if "cms.plugins.text" in settings.INSTALLED_APPS:
    from cms.tests.plugins import PluginsTestCase
    if "reversion" in settings.INSTALLED_APPS:
        from cms.tests.reversion_tests import ReversionTestCase
from cms.tests.plugins import PluginManyToManyTestCase
from cms.tests.reversion_tests import ReversionTestCase
        
from cms.tests.menu import MenusTestCase
from cms.tests.rendering import RenderingTestCase
from cms.tests.placeholder import PlaceholderTestCase
from cms.tests.docs import DocsTestCase

settings.CMS_PERMISSION = True
settings.CMS_MODERATOR = True
settings.CMS_NAVIGATION_EXTENDERS = (
    ('testapp.sampleapp.menu_extender.get_nodes', 'SampleApp Menu'),
)

settings.CMS_FLAT_URLS = False
settings.CMS_MENU_TITLE_OVERWRITE = True
settings.CMS_HIDE_UNTRANSLATED = False
settings.CMS_URL_OVERWRITE = True
if not "testapp.sampleapp" in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ["testapp.sampleapp"]

def suite():
    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(urlutils))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PagesTestCase))
    
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(SiteTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(NavExtenderTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(NonRootCase))
    if "cms.plugins.text" in settings.INSTALLED_APPS:
        s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PluginsTestCase))
        if "reversion" in settings.INSTALLED_APPS:
            s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(ReversionTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PermissionModeratorTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(MenusTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(RenderingTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PlaceholderTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(DocsTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PluginManyToManyTestCase))
    
    return s
