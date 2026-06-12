import json
import os
import tempfile
import urllib.error
from io import StringIO
from unittest import mock

from django.core.management import CommandError
from django.test import SimpleTestCase

from cms.management.commands.startcmsproject import Command

MANAGE_PY = """#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
"""

SETTINGS_PY = '''"""Django settings for mysite project."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "test-secret-key"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mysite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LANGUAGE_CODE = "en-us"
'''

OLD_STYLE_SETTINGS_PY = SETTINGS_PY.replace(
    "from pathlib import Path\n\nBASE_DIR = Path(__file__).resolve().parent.parent",
    "import os\n\nBASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
)

URLS_PY = """from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
"""

DEFAULT_OPTIONS = {
    "interactive": False,
    "mode": "traditional",
    "versioning": True,
    "moderation": False,
    "alias": True,
    "stories": False,
}


def bundled_rules(**extra):
    import cms.management.commands.startcmsproject as command_module

    path = os.path.join(os.path.dirname(command_module.__file__), Command.INSTALL_RULES_FILENAME)
    with open(path, encoding="utf-8") as handle:
        rules = json.load(handle)
    rules.update(extra)
    return rules


def make_command():
    return Command(stdout=StringIO(), stderr=StringIO(), no_color=True)


class LoadInstallRulesTests(SimpleTestCase):
    def test_metadata_keys_are_ignored(self):
        """A ``$schema`` entry (and any other ``$``-prefixed key) is dropped."""
        payload = json.dumps(bundled_rules(**{"$schema": "https://example.com/schema.json"})).encode()
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = payload
        command = make_command()
        with mock.patch("urllib.request.urlopen", return_value=response):
            rules = command.load_install_rules()
        self.assertNotIn("$schema", rules)
        self.assertIn("installed_apps", rules)

    def test_falls_back_to_bundled_rules(self):
        command = make_command()
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
            rules = command.load_install_rules()
        self.assertIn("installed_apps", rules)
        self.assertIn("using bundled defaults", command.stderr.getvalue())

    def test_non_object_rules_raise(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'["not", "a", "dict"]'
        command = make_command()
        with mock.patch("urllib.request.urlopen", return_value=response):
            with self.assertRaises(CommandError):
                command.load_install_rules()


class EditingHelperTests(SimpleTestCase):
    def test_insert_into_list_appends_missing_items(self):
        text, added = Command._insert_into_list(SETTINGS_PY, "INSTALLED_APPS", ["cms", "django.contrib.auth"])
        self.assertEqual(added, ["cms"])  # existing entries are not duplicated
        self.assertIn('    "cms",\n]', text)

    def test_insert_into_inline_list(self):
        text, added = Command._insert_into_list(SETTINGS_PY, "DIRS", ['BASE_DIR / "templates"'], quote=False)
        self.assertEqual(added, ['BASE_DIR / "templates"'])
        self.assertIn('BASE_DIR / "templates",', text)

    def test_insert_near_anchor_before_and_after(self):
        text, added = make_command()._insert_near_anchor(
            SETTINGS_PY, "djangocms_simple_admin_style", "django.contrib.admin", before=True
        )
        self.assertEqual(added, ["djangocms_simple_admin_style"])
        self.assertLess(text.index("djangocms_simple_admin_style"), text.index("django.contrib.admin"))

        text, added = make_command()._insert_near_anchor(
            text,
            "django.middleware.locale.LocaleMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
        )
        self.assertEqual(added, ["django.middleware.locale.LocaleMiddleware"])
        self.assertLess(
            text.index("django.contrib.sessions.middleware.SessionMiddleware"),
            text.index("django.middleware.locale.LocaleMiddleware"),
        )

    def test_insert_near_anchor_falls_back_to_append(self):
        text, added = make_command()._insert_near_anchor(
            SETTINGS_PY, "cms", "no.such.entry", list_name="INSTALLED_APPS"
        )
        self.assertEqual(added, ["cms"])
        self.assertIn('    "cms",\n]', text)

    def test_ensure_include_import(self):
        text = Command._ensure_include_import(URLS_PY)
        self.assertIn("from django.urls import include", text)
        # Already present: unchanged
        self.assertEqual(Command._ensure_include_import(text), text)

    def test_get_settings_module_and_urlconf(self):
        command = make_command()
        with tempfile.TemporaryDirectory() as tmp:
            manage_py = os.path.join(tmp, "manage.py")
            with open(manage_py, "w", encoding="utf-8") as handle:
                handle.write(MANAGE_PY)
            self.assertEqual(command.get_settings_module(manage_py), "mysite.settings")
        self.assertEqual(command.get_urlconf(SETTINGS_PY, "mysite.settings"), "mysite.urls")
        self.assertEqual(command.get_urlconf("", "mysite.settings"), "mysite.urls")

    def test_rule_applies(self):
        options = {"versioning": True, "mode": "headless"}
        self.assertTrue(Command._rule_applies(None, options))
        self.assertTrue(Command._rule_applies({"flag": "versioning"}, options))
        self.assertFalse(Command._rule_applies({"flag": "stories"}, options))
        self.assertTrue(Command._rule_applies({"mode": ["headless", "hybrid"]}, options))
        self.assertFalse(Command._rule_applies({"mode": ["traditional"]}, options))
        self.assertFalse(Command._rule_applies({"flag": "versioning", "mode": ["traditional"]}, options))


class PackageDerivationTests(SimpleTestCase):
    def test_dotted_apps_resolve_to_their_top_level_package(self):
        command = make_command()
        command.install_packages = mock.Mock()
        command.run_management_command = mock.Mock()
        apps = [
            "cms",
            "filer",
            "djangocms_frontend",
            "djangocms_frontend.contrib.grid",
            "djangocms_frontend.contrib.image",
            "rest_framework",
            "djangocms_rest",
        ]
        packages_map = {"filer": "django-filer", "rest_framework": "djangorestframework"}
        command._finish_existing_project(apps, packages_map, {"interactive": False})
        packages = command.install_packages.call_args.args[0]
        self.assertEqual(
            packages,
            ["django-cms", "django-filer", "djangocms-frontend", "djangorestframework", "djangocms-rest"],
        )


class AddToExistingProjectTests(SimpleTestCase):
    """Run ``djangocms .`` against a synthetic ``django-admin startproject`` layout."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project_dir = self.tmp.name
        self._old_cwd = os.getcwd()
        self.addCleanup(os.chdir, self._old_cwd)

        package_dir = os.path.join(self.project_dir, "mysite")
        os.makedirs(package_dir)
        self._write(os.path.join(self.project_dir, "manage.py"), MANAGE_PY)
        self._write(os.path.join(package_dir, "__init__.py"), "")
        self._write(os.path.join(package_dir, "settings.py"), SETTINGS_PY)
        self._write(os.path.join(package_dir, "urls.py"), URLS_PY)
        os.chdir(self.project_dir)

    @staticmethod
    def _write(path, text):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    @staticmethod
    def _read(path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def run_command(self, **option_overrides):
        command = make_command()
        command.load_install_rules = mock.Mock(return_value=bundled_rules())
        command._finish_existing_project = mock.Mock()
        options = {**DEFAULT_OPTIONS, **option_overrides}
        command.add_to_existing_project(options)
        return command

    def test_traditional_mode(self):
        command = self.run_command()

        settings_text = self._read("mysite/settings.py")
        for app in (
            '"cms",',
            '"menus",',
            '"djangocms_frontend",',
            '"djangocms_frontend.contrib.grid",',
            '"djangocms_versioning",',
            '"djangocms_alias",',
        ):
            self.assertIn(app, settings_text)
        self.assertNotIn("djangocms_moderation", settings_text)
        self.assertNotIn("djangocms_stories", settings_text)
        self.assertNotIn("djangocms_rest", settings_text)

        # Positional inserts
        self.assertLess(
            settings_text.index("djangocms_simple_admin_style"), settings_text.index("django.contrib.admin")
        )
        self.assertLess(
            settings_text.index("django.contrib.sessions.middleware.SessionMiddleware"),
            settings_text.index("django.middleware.locale.LocaleMiddleware"),
        )

        self.assertIn("sekizai.context_processors.sekizai", settings_text)
        self.assertIn("SITE_ID = 1", settings_text)
        self.assertIn("CMS_TEMPLATES", settings_text)
        self.assertNotIn("CMS_PLACEHOLDERS", settings_text)
        self.assertIn('BASE_DIR / "templates"', settings_text)
        self.assertTrue(os.path.isfile("templates/cms-base.html"))

        urls_text = self._read("mysite/urls.py")
        self.assertIn("from django.urls import include", urls_text)
        self.assertIn('path("", include("cms.urls"))', urls_text)
        self.assertNotIn("djangocms_rest", urls_text)

        # The dotted frontend apps must reach the package resolution step.
        apps = command._finish_existing_project.call_args.args[0]
        self.assertIn("djangocms_frontend.contrib.grid", apps)

    def test_headless_mode(self):
        self.run_command(mode="headless")

        settings_text = self._read("mysite/settings.py")
        self.assertIn('"djangocms_rest",', settings_text)
        self.assertIn('"rest_framework",', settings_text)
        self.assertIn("CMS_PLACEHOLDERS", settings_text)
        self.assertNotIn("CMS_TEMPLATES", settings_text)
        self.assertFalse(os.path.isdir("templates"))

        urls_text = self._read("mysite/urls.py")
        self.assertIn('path("api/", include("djangocms_rest.urls"))', urls_text)
        self.assertNotIn('include("cms.urls")', urls_text)

    def test_rerun_is_idempotent(self):
        self.run_command()
        settings_text = self._read("mysite/settings.py")
        urls_text = self._read("mysite/urls.py")

        self.run_command()
        self.assertEqual(self._read("mysite/settings.py"), settings_text)
        self.assertEqual(self._read("mysite/urls.py"), urls_text)

    def test_old_style_base_dir(self):
        self._write("mysite/settings.py", OLD_STYLE_SETTINGS_PY)
        self.run_command()
        settings_text = self._read("mysite/settings.py")
        self.assertIn('os.path.join(BASE_DIR, "templates")', settings_text)
        self.assertNotIn('BASE_DIR / "templates"', settings_text)

    def test_schema_entry_in_rules_is_harmless(self):
        command = make_command()
        command.load_install_rules = mock.Mock(
            return_value=bundled_rules(**{"$schema": "https://example.com/schema.json"})
        )
        command._finish_existing_project = mock.Mock()
        command.add_to_existing_project(dict(DEFAULT_OPTIONS))
        self.assertIn('"cms",', self._read("mysite/settings.py"))

    def test_missing_manage_py(self):
        os.remove("manage.py")
        with self.assertRaises(CommandError):
            self.run_command()


class HandleValidationTests(SimpleTestCase):
    def test_moderation_requires_versioning(self):
        command = make_command()
        options = {
            "name": "mysite",
            "directory": None,
            "interactive": False,
            "prompt": False,
            "template": None,
            "mode": "traditional",
            "versioning": False,
            "moderation": True,
            "alias": None,
            "stories": None,
        }
        with self.assertRaises(CommandError) as raised:
            command.handle(**options)
        self.assertIn("moderation requires versioning", str(raised.exception))

    def test_missing_name_with_noinput(self):
        command = make_command()
        options = {
            "name": None,
            "directory": None,
            "interactive": False,
            "prompt": False,
            "template": None,
            "mode": None,
            "versioning": None,
            "moderation": None,
            "alias": None,
            "stories": None,
        }
        with self.assertRaises(CommandError) as raised:
            command.handle(**options)
        self.assertEqual(str(raised.exception), Command.missing_args_message)
