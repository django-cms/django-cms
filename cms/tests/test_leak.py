# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from django.core.urlresolvers import reverse
from django.test import Client

class ATestLeakCase(CMSTestCase):
    """
    This must run as the first testcase to demonstrate the issue
    In fact we have a double issue:
    * non-root CMS urlconf is not mapped correctly at tests start:
      reverse('pages-root') doesn't return '/content/' (in this testcase)
      as it should
    * whenever a Client.get() is made to a non-existing URL, CMS urlconf is fixed
      and reverse() correctly maps to CMS URLs

    """
    urls = 'cms.test_utils.project.nonroot_urls'

    def setUp(self):
        self.page1 = create_page("page1", "nav_playground.html", "en",
                                 published=True, in_navigation=True)

    def test_1_reverse_issue(self):
        """ As we load nonroot_urls CMS should start at /content/

        """
        rev1 = reverse("pages-root")
        self.assertEquals(rev1, "/content/")

    def test_3_reverse_issue(self):
        """ Identical test as test_1_reverse_issue but executed after
        test_2_basic_wtf, it passes
        """
        rev1 = reverse("pages-root")
        self.assertEquals(rev1, "/content/")

    def test_2_basic_wtf(self):
        """ This demostrates a flaw in some url registration problem.
        The two identical code blocks should run just fine and give the same
        result.
        As of issue #1335 this is not the case

        """
        with SettingsOverride(CMS_MODERATOR=False):
            ## Run 1
            cl1 = Client()
            rev1 = reverse("pages-root")
            # The assert below should fail, but it passes due to some url
            # mapping issue as demoed in test_1_reverse_issue
            self.assertEquals(rev1, "/")
            # Here come the magic
            # after this failed request CMS url are mapped correctly and the
            # code block at Run 2 correctly fails.
            # Any URL would do here, given it raises a 404
            # rev1 = "/wtf-this-page-does-not-exists/"
            response = cl1.get(rev1)
            self.assertEquals(response.status_code, 404)

            ## Run 2
            cl2 = Client()
            rev2 = reverse("pages-root")
            self.assertEquals(rev2, "/")
            response = cl2.get(rev2)
            self.assertEquals(response.status_code, 404)
