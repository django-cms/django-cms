# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.test_utils.compat import skipIf
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import TemporaryDirectory
from sphinx.application import Sphinx
import cms
import os
import socket
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

ROOT_DIR = os.path.dirname(cms.__file__)
DOCS_DIR = os.path.abspath(os.path.join(ROOT_DIR, '..', 'docs'))


def has_no_internet():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('4.4.4.2', 80))
    except socket.error: # no internet
        return  True
    return False


class DocsTestCase(CMSTestCase):
    """
    Test docs building correctly for HTML
    """
    @skipIf(has_no_internet(), "No internet")
    def test_html(self):
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
