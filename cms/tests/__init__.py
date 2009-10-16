# -*- coding: utf-8 -*-
import unittest
import doctest
from django.conf import settings


# doc testing in some modules
from cms.utils import urlutils
from cms.tests.page import PagesTestCase
from cms.tests.permmod import PermissionModeratorTestCase
from cms.tests.site import SiteTestCase

def suite():
    # this must be changed!! and tests must happen for multiple configurations!
    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(urlutils))
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PagesTestCase))
    
    s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(SiteTestCase))
    
    if settings.CMS_PERMISSION and settings.CMS_MODERATOR:
        # this test is settings dependant, and these settings can not be
        # changed on the fly.
        s.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(PermissionModeratorTestCase))
    return s

