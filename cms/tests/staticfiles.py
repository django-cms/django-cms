from __future__ import with_statement
from cms.test_utils.compat import skipIf
from cms.test_utils.util.context_managers import SettingsOverride, StdoutOverride, TemporaryDirectory
import django
from django.core import management
from django.test import TestCase
from distutils.version import LooseVersion


class StaticFilesTest(TestCase):

    @skipIf(LooseVersion(django.get_version()) < LooseVersion('1.4'),
            "CachedStaticFilesStorage doesn't exist in Django < 1.4")
    def test_collectstatic_with_cached_static_files_storage(self):
        # CachedStaticFilesStorage requires that the CSS files
        # don't contain any broken links.
        with TemporaryDirectory() as tmpdir:
            with SettingsOverride(STATIC_ROOT=tmpdir,
                STATICFILES_STORAGE='django.contrib.staticfiles.storage.CachedStaticFilesStorage'):
                with StdoutOverride() as output:
                    management.call_command('collectstatic', interactive=False)

