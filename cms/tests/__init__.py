# -*- coding: utf-8 -*-
from cms.tests.moderator import ModeratorTestCase
import unittest
import doctest

# doc testing in some modules
from cms.utils import urlutils
from cms.tests.page import PagesTestCase
from cms.tests.permmod import PermissionModeratorTestCase
from cms import settings as cms_settings

def suite():
    # this must be changed!! and tests must happen for multiple configurations!
    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(urlutils))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PagesTestCase))
    
    if cms_settings.CMS_PERMISSION and cms_settings.CMS_MODERATOR:
        s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PermissionModeratorTestCase))
    elif cms_settings.CMS_PERMISSION and not cms_settings.CMS_MODERATOR:
        pass
    elif not cms_settings.CMS_PERMISSION and cms_settings.CMS_MODERATOR:
        s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(ModeratorTestCase))
    return s
