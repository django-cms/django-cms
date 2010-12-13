from __future__ import with_statement
from cms.tests.base import CMSTestCase
from django.conf import settings
from shutil import rmtree as _rmtree
from sphinx.application import Sphinx
from tempfile import template, mkdtemp, _exists
import os
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

ROOT_DIR = os.path.join(settings.PROJECT_DIR, '..', '..')
DOCS_DIR = os.path.join(ROOT_DIR, 'docs')

class TemporaryDirectory:
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everthing contained
    in it are removed.
    """

    def __init__(self, suffix="", prefix=template, dir=None):
        self.name = mkdtemp(suffix, prefix, dir)

    def __enter__(self):
        return self.name

    def cleanup(self):
        if _exists(self.name):
            _rmtree(self.name)

    def __exit__(self, exc, value, tb):
        self.cleanup()


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