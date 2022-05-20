import io
import os
import socket
import sys
from contextlib import contextmanager
from unittest import skipIf, skipUnless

from sphinx.application import Sphinx
from sphinx.errors import SphinxWarning

try:
    import enchant
except ImportError:
    enchant = None

import cms
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import TemporaryDirectory

ROOT_DIR = os.path.dirname(cms.__file__)
DOCS_DIR = os.path.abspath(os.path.join(ROOT_DIR, u'..', u'docs'))


def has_no_internet():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(5)
        s.connect(('4.4.4.2', 80))
        s.send(b"hello")
    except socket.error:  # no internet
        return True
    return False


@contextmanager
def tmp_list_append(lst, x):
    lst.append(x)
    try:
        yield
    finally:
        if x in lst:
            lst.remove(x)


class DocsTestCase(CMSTestCase):
    """
    Test docs building correctly for HTML
    """
    @skipIf(has_no_internet(), "No internet")
    def test_html(self):
        status = io.StringIO()
        with TemporaryDirectory() as OUT_DIR:
            app = Sphinx(
                srcdir=DOCS_DIR,
                confdir=DOCS_DIR,
                outdir=OUT_DIR,
                doctreedir=OUT_DIR,
                buildername="html",
                warningiserror=True,
                status=status,
            )
            try:
                app.build()
            except:  # noqa: E722
                print(status.getvalue())
                raise

    @skipIf(has_no_internet(), "No internet")
    @skipIf(enchant is None, "Enchant not installed")
    @skipUnless(os.environ.get('TEST_DOCS') == '1', 'Skipping for simplicity')
    def test_spelling(self):
        status = io.StringIO()
        with TemporaryDirectory() as OUT_DIR:
            with tmp_list_append(sys.argv, 'spelling'):
                try:
                    app = Sphinx(
                        srcdir=DOCS_DIR,
                        confdir=DOCS_DIR,
                        outdir=OUT_DIR,
                        doctreedir=OUT_DIR,
                        buildername="spelling",
                        warningiserror=True,
                        status=status,
                        confoverrides={
                            'extensions': [
                                'djangocms',
                                'sphinx.ext.intersphinx',
                                'sphinxcontrib.spelling'
                            ]
                        }
                    )
                    app.build()
                    self.assertEqual(app.statuscode, 0, status.getvalue())
                except SphinxWarning:
                    # while normally harmless, causes a test failure
                    pass
                except:  # noqa: E722
                    print(status.getvalue())
                    raise
