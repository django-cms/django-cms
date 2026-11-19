import os
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from cms.utils.mptree import get_tree_backend, treebeard_is_supported
from cms.utils.setup import validate_dependencies

SUPPORTED_TREEBEARD = ("4.3", "5.3.1")
UNSUPPORTED_TREEBEARD = ("6.0rc1", "6.0", "6.0.1", "7.0.2", "8.0")


def treebeard_version(value):
    return patch("importlib.metadata.version", return_value=value)


@contextmanager
def no_backend_selected():
    """Neither the setting nor the env var selects a tree backend."""
    with override_settings(), patch.dict(os.environ):
        os.environ.pop("CMS_TREE_BACKEND", None)
        if hasattr(settings, "CMS_TREE_BACKEND"):
            del settings.CMS_TREE_BACKEND
        yield


class TreeBackendDependencyTests(SimpleTestCase):
    @override_settings(CMS_TREE_BACKEND="treebeard")
    @patch("cms.utils.setup.app_is_installed", return_value=True)
    def test_treebeard_version_compatibility(self, installed):
        for version in SUPPORTED_TREEBEARD:
            with self.subTest(version=version), treebeard_version(version):
                validate_dependencies()

        for version in UNSUPPORTED_TREEBEARD:
            with self.subTest(version=version), treebeard_version(version):
                # An explicit choice is never overridden.
                self.assertEqual(get_tree_backend(), "treebeard")
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
    @patch("importlib.metadata.version")
    def test_mptree_does_not_require_treebeard(self, version, installed):
        validate_dependencies()
        installed.assert_not_called()
        version.assert_not_called()


class DefaultTreeBackendTests(SimpleTestCase):
    """Without an explicit choice the backend follows the installed treebeard."""

    def test_supported_treebeard_keeps_treebeard_backend(self):
        for version in SUPPORTED_TREEBEARD:
            with self.subTest(version=version), no_backend_selected(), treebeard_version(version):
                self.assertEqual(get_tree_backend(), "treebeard")

    @patch("cms.utils.setup.app_is_installed")
    def test_unsupported_treebeard_falls_back_to_mptree(self, installed):
        for version in UNSUPPORTED_TREEBEARD:
            with self.subTest(version=version), no_backend_selected(), treebeard_version(version):
                self.assertEqual(get_tree_backend(), "mptree")
                # The fallback must start up instead of raising.
                validate_dependencies()
        installed.assert_not_called()

    def test_env_var_is_an_explicit_choice(self):
        with no_backend_selected(), treebeard_version("7.0.2"):
            with patch.dict(os.environ, {"CMS_TREE_BACKEND": "treebeard"}):
                self.assertEqual(get_tree_backend(), "treebeard")

    def test_missing_or_invalid_metadata_keeps_treebeard_backend(self):
        with no_backend_selected():
            with patch("importlib.metadata.version", side_effect=PackageNotFoundError("django-treebeard")):
                self.assertTrue(treebeard_is_supported())
                self.assertEqual(get_tree_backend(), "treebeard")
            with treebeard_version("not a version"):
                self.assertTrue(treebeard_is_supported())
