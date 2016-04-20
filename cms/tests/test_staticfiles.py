from __future__ import with_statement

from django.core import management
from django.test import TestCase

from cms.test_utils.util.context_managers import StdoutOverride
from cms.test_utils.util.context_managers import TemporaryDirectory


class StaticFilesTest(TestCase):

    def test_collectstatic_with_cached_static_files_storage(self):
        # CachedStaticFilesStorage requires that the CSS files
        # don't contain any broken links.
        with TemporaryDirectory() as tmpdir:
            with self.settings(STATIC_ROOT=tmpdir,
                STATICFILES_STORAGE='django.contrib.staticfiles.storage.CachedStaticFilesStorage'):
                with StdoutOverride():
                    management.call_command('collectstatic', interactive=False)
