from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from cms.utils.setup import validate_dependencies


class TreeBackendDependencyTests(SimpleTestCase):
    @override_settings(CMS_TREE_BACKEND="treebeard")
    @patch("cms.utils.setup.app_is_installed", return_value=True)
    def test_treebeard_version_compatibility(self, installed):
        for treebeard_version in ("4.3", "5.3.1"):
            with self.subTest(version=treebeard_version), patch(
                "cms.utils.setup.version", return_value=treebeard_version
            ):
                validate_dependencies()

        for treebeard_version in ("6.0rc1", "6.0", "6.0.1", "7.0.2", "8.0"):
            with self.subTest(version=treebeard_version), patch(
                "cms.utils.setup.version", return_value=treebeard_version
            ):
                with self.assertRaisesMessage(
                    ImproperlyConfigured,
                    'Set CMS_TREE_BACKEND = "mptree", or install django-treebeard<6.',
                ):
                    validate_dependencies()

    @override_settings(CMS_TREE_BACKEND="treebeard")
    @patch("cms.utils.setup.app_is_installed", return_value=False)
    def test_treebeard_backend_requires_installed_app(self, installed):
        with self.assertRaisesMessage(ImproperlyConfigured, "django CMS requires django-treebeard."):
            validate_dependencies()

    @override_settings(CMS_TREE_BACKEND="mptree")
    @patch("cms.utils.setup.app_is_installed")
    @patch("cms.utils.setup.version")
    def test_mptree_does_not_require_treebeard(self, treebeard_version, installed):
        validate_dependencies()
        installed.assert_not_called()
        treebeard_version.assert_not_called()
