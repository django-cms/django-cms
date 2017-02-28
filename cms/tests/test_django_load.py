# -*- coding: utf-8 -*-
from collections import Iterator

from cms.test_utils.testcases import CMSTestCase
from cms.utils import django_load
from cms.utils.conf import get_cms_setting


class DjangoLoadTestCase(CMSTestCase):
    def test_iterators(self):
        self.assertIsInstance(django_load.iterload('menus'), Iterator)
        toolbars = get_cms_setting('TOOLBARS')
        self.assertIsInstance(django_load.iterload_objects(toolbars), Iterator)
