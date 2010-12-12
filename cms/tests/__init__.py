# -*- coding: utf-8 -*-
from cms.tests.admin import AdminTestCase
from cms.tests.apphooks import ApphooksTestCase
from cms.tests.docs import DocsTestCase
from cms.tests.menu import MenusTestCase
from cms.tests.navextender import NavExtenderTestCase
from cms.tests.nonroot import NonRootCase
from cms.tests.page import PagesTestCase
from cms.tests.permmod import PermissionModeratorTestCase
from cms.tests.placeholder import PlaceholderTestCase
from cms.tests.plugins import PluginManyToManyTestCase, PluginsTestCase
from cms.tests.rendering import RenderingTestCase
from cms.tests.reversion_tests import ReversionTestCase
from cms.tests.site import SiteTestCase
from cms.utils import urlutils
import doctest
import unittest


def suite():
    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(urlutils))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PagesTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(SiteTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(NavExtenderTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(NonRootCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PluginsTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(ReversionTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PermissionModeratorTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(MenusTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(RenderingTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PlaceholderTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(DocsTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PluginManyToManyTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(ApphooksTestCase))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(AdminTestCase))
    return s
