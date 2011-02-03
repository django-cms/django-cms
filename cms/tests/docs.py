# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.test.testcases import CMSTestCase
from cms.test.util.context_managers import TemporaryDirectory
from django.conf import settings
from sphinx.application import Sphinx
import os
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

ROOT_DIR = os.path.join(settings.PROJECT_DIR, '..', '..', '..')
DOCS_DIR = os.path.join(ROOT_DIR, 'docs')


class DocsTestCase(CMSTestCase):
    """
    Test docs building correctly for HTML
    """
    def test_01_html(self):
        nullout = StringIO()
        with TemporaryDirectory() as OUT_DIR:
            app = Sphinx(
                DOCS_DIR,
                DOCS_DIR,
                OUT_DIR,
                OUT_DIR,
                "html",
                warningiserror=True,
                status=nullout,
            )
            try:
                app.build()
            except:
                print nullout.getvalue()
                raise
