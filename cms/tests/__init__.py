# -*- coding: utf-8 -*-
import unittest
import doctest

# doc testing in some modules
from cms.utils import urlutils
from cms.tests.page import PagesTestCase
from cms.tests.permmod import PermissionModerationTestCase
from cms import settings as cms_settings

def suite(result=None):
    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(urlutils))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PagesTestCase))
    
    if cms_settings.CMS_PERMISSION and cms_settings.CMS_MODERATOR:
        # this must be changed!
        s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PermissionModerationTestCase))
    return s
