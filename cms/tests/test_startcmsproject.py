import io
import json
import os
import sys
import tarfile
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

COMPUTED_APPS_SETTINGS_PY = SETTINGS_PY.replace(
    """INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]""",
    """DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = []
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS""",
)

URLS_PY = """from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
"""

URLS_PY_I18N = """from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]

urlpatterns += i18n_patterns(
    path("accounts/", include("accounts.urls")),
)
"""

DEFAULT_OPTIONS = {
    "interactive": False,
    "mode": "traditional",
    "versioning": True,
    "moderation": False,
    "alias": True,
    "stories": False,
    "history": False,
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
    def test_loads_rules_from_custom_template_directory(self):
        rules = bundled_rules()
        rules["installed_apps"] = [{"items": ["agency_app"]}]
        with tempfile.TemporaryDirectory() as template:
            with open(os.path.join(template, Command.INSTALL_RULES_FILENAME), "w", encoding="utf-8") as rules_file:
                json.dump(rules, rules_file)
            command = make_command()
            command._requested_template = template
            with mock.patch("urllib.request.urlopen") as urlopen:
                loaded = command.load_install_rules()
        self.assertEqual(loaded["installed_apps"], [{"items": ["agency_app"]}])
        urlopen.assert_not_called()

    def test_loads_rules_from_custom_remote_template_archive(self):
        rules = bundled_rules()
        rules["installed_apps"] = [{"items": ["remote_agency_app"]}]
        archive = io.BytesIO()
        payload = json.dumps(rules).encode()
        with tarfile.open(fileobj=archive, mode="w:gz") as template_tar:
            member = tarfile.TarInfo(f"agency-template/{Command.INSTALL_RULES_FILENAME}")
            member.size = len(payload)
            template_tar.addfile(member, io.BytesIO(payload))
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = archive.getvalue()
        command = make_command()
        command._requested_template = "https://example.com/agency-template.tar.gz"
        with mock.patch("urllib.request.urlopen", return_value=response) as urlopen:
            loaded = command.load_install_rules()
        self.assertEqual(loaded["installed_apps"], [{"items": ["remote_agency_app"]}])
        urlopen.assert_called_once_with("https://example.com/agency-template.tar.gz", timeout=15)

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

    def test_can_force_bundled_rules(self):
        command = make_command()
        command._use_bundled_install_rules = True
        with mock.patch("urllib.request.urlopen") as urlopen:
            rules = command.load_install_rules()
        self.assertIn("installed_apps", rules)
        urlopen.assert_not_called()

    def test_fetched_rules_without_options_use_bundled_options(self):
        rules = bundled_rules()
        rules.pop("options")
        rules["installed_apps"] = [{"items": ["remote_app"]}]
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(rules).encode()
        command = make_command()
        with mock.patch("urllib.request.urlopen", return_value=response):
            loaded = command.load_install_rules()
        self.assertIn("options", loaded)
        self.assertEqual(loaded["installed_apps"], [{"items": ["remote_app"]}])

    def test_non_object_rules_raise(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'["not", "a", "dict"]'
        command = make_command()
        with mock.patch("urllib.request.urlopen", return_value=response):
            with self.assertRaises(CommandError):
                command.load_install_rules()

    def test_unknown_option_flag_raises(self):
        rules = bundled_rules(installed_apps=[{"items": ["cms"], "when": {"flag": "unknown"}}])
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(rules).encode()
        command = make_command()
        with mock.patch("urllib.request.urlopen", return_value=response):
            with self.assertRaises(CommandError) as raised:
                command.load_install_rules()
        self.assertIn("unknown option flag", str(raised.exception))


class ParserOptionTests(SimpleTestCase):
    def test_custom_template_defines_command_options(self):
        rules = bundled_rules()
        rules["options"]["agency_feature"] = {
            "type": "boolean",
            "default": False,
            "label": "Agency feature",
            "help": "Install the agency feature.",
        }
        with tempfile.TemporaryDirectory() as template:
            with open(os.path.join(template, Command.INSTALL_RULES_FILENAME), "w", encoding="utf-8") as rules_file:
                json.dump(rules, rules_file)
            command = make_command()
            with mock.patch.object(sys, "argv", ["djangocms", "mysite", "--template", template]):
                parser = command.create_parser("djangocms", "")
            parsed = parser.parse_args(["mysite", "--template", template, "--agency-feature"])
        self.assertTrue(parsed.agency_feature)

    def test_template_options_are_added_from_rules(self):
        command = make_command()
        command.load_install_rules = mock.Mock(return_value=bundled_rules())
        parser = command.create_parser("djangocms", "")
        parsed = parser.parse_args(["mysite", "--mode", "headless", "--no-versioning", "--stories", "--history"])
        self.assertEqual(parsed.mode, "headless")
        self.assertFalse(parsed.versioning)
        self.assertTrue(parsed.stories)
        self.assertTrue(parsed.history)

    def test_use_bundled_rules_option_skips_fetch_while_building_parser(self):
        command = make_command()
        with mock.patch.object(sys, "argv", ["djangocms", "--use-bundled-install-rules"]), mock.patch(
            "urllib.request.urlopen"
        ) as urlopen:
            parser = command.create_parser("djangocms", "")
        parsed = parser.parse_args(["mysite", "--use-bundled-install-rules"])
        self.assertTrue(parsed.use_bundled_install_rules)
        urlopen.assert_not_called()


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

    def test_uses_i18n_patterns_detects_usage_not_import(self):
        # The bare import must not count as usage.
        self.assertFalse(Command._uses_i18n_patterns("from django.conf.urls.i18n import i18n_patterns\n"))
        self.assertTrue(Command._uses_i18n_patterns(URLS_PY_I18N))
        self.assertFalse(Command._uses_i18n_patterns(URLS_PY))

    def test_append_i18n_patterns_adds_block(self):
        text, added = Command._append_i18n_patterns(URLS_PY_I18N, ['path("", include("cms.urls"))'])
        self.assertEqual(added, ['path("", include("cms.urls"))'])
        self.assertIn('urlpatterns += i18n_patterns(\n    path("", include("cms.urls")),\n)', text)
        # The CMS catch-all is appended last, after the project's own i18n block.
        self.assertLess(text.index('include("accounts.urls")'), text.index('include("cms.urls")'))

    def test_insert_import_after_existing_imports(self):
        text = "from pathlib import Path\nimport sys\n\nBASE_DIR = Path()\n"
        result = Command._insert_import(text, "import os")
        self.assertEqual(result, "from pathlib import Path\nimport sys\nimport os\n\nBASE_DIR = Path()\n")

    def test_insert_import_skips_module_preamble(self):
        # Without existing imports, the statement must not land before the
        # shebang, encoding comment, docstring or __future__ imports.
        text = (
            "#!/usr/bin/env python\n"
            "# -*- coding: utf-8 -*-\n"
            '"""Module docstring.\n\nspanning lines.\n"""\n'
            "from __future__ import annotations\n\n"
            "BASE_DIR = 1\n"
        )
        result = Command._insert_import(text, "import os")
        self.assertIn("from __future__ import annotations\nimport os\n", result)
        self.assertTrue(result.startswith("#!/usr/bin/env python\n"))

    def test_insert_import_after_single_line_docstring(self):
        text = '"""Settings."""\nBASE_DIR = 1\n'
        result = Command._insert_import(text, "import os")
        self.assertEqual(result, '"""Settings."""\nimport os\nBASE_DIR = 1\n')

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
            "djangocms_history",
        ]
        packages_map = {
            "filer": "django-filer",
            "djangocms_history": "djangocms-history>=3",
            "rest_framework": "djangorestframework",
        }
        command._finish_existing_project(apps, packages_map, {"interactive": False})
        packages = command.install_packages.call_args.args[0]
        self.assertEqual(
            packages,
            [
                "django-cms",
                "django-filer",
                "djangocms-frontend",
                "djangorestframework",
                "djangocms-rest",
                "djangocms-history>=3",
            ],
        )

    def test_install_packages_rejects_unexpected_characters(self):
        command = make_command()
        for bad in ["django-cms; rm -rf /", "pkg==1.0", "foo bar", "evil$(whoami)", "a/b"]:
            with self.assertRaises(CommandError):
                command.install_packages([bad])

    def test_install_packages_accepts_lower_bound_specs(self):
        command = make_command()
        with mock.patch.object(command, "running_in_venv", return_value=True), mock.patch("subprocess.run") as run:
            run.return_value.returncode = 0
            command.install_packages(["djangocms-history>=3"])
        run.assert_called_once()

    def test_install_packages_refuses_outside_venv(self):
        # Outside a virtual environment (and without the opt-out env var) the
        # command refuses to pip install and prints the manual command instead.
        command = make_command()
        with mock.patch.object(command, "running_in_venv", return_value=False), mock.patch.dict(
            os.environ, {"DJANGOCMS_ALLOW_PIP_INSTALL": "False"}
        ):
            with self.assertRaises(CommandError):
                command.install_packages(["django-cms"])
        self.assertIn("virtual environment", command.stderr.getvalue())

    def test_finish_existing_project_dry_run_skips_install(self):
        command = make_command()
        command.install_packages = mock.Mock()
        command.run_management_command = mock.Mock()
        command._finish_existing_project(["cms"], {}, {"interactive": False, "dry_run": True})
        command.install_packages.assert_not_called()
        command.run_management_command.assert_not_called()
        self.assertIn("Dry run: would install", command.stdout.getvalue())

    def test_finish_existing_project_can_skip_install(self):
        # Declining the install prompt prints the manual follow-up steps and
        # neither installs packages nor runs migrations.
        command = make_command()
        command.install_packages = mock.Mock()
        command.run_management_command = mock.Mock()
        command.ask_bool = mock.Mock(return_value=False)
        command._finish_existing_project(["cms"], {}, {"interactive": True})
        command.install_packages.assert_not_called()
        command.run_management_command.assert_not_called()
        self.assertIn("Install them later", command.stdout.getvalue())


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
        self.assertNotIn("djangocms_history", settings_text)
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

    def test_history_option(self):
        command = self.run_command(history=True)

        settings_text = self._read("mysite/settings.py")
        self.assertIn('"djangocms_history",', settings_text)

        apps = command._finish_existing_project.call_args.args[0]
        packages_map = command._finish_existing_project.call_args.args[1]
        self.assertIn("djangocms_history", apps)
        self.assertEqual(packages_map["djangocms_history"], "djangocms-history>=3")

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

    def test_cms_urls_go_into_i18n_patterns_when_used(self):
        # A project whose urls.py already uses i18n_patterns must get the CMS
        # catch-all routed through i18n_patterns (so pages keep a language
        # prefix), while non-i18n routes stay in the plain urlpatterns list.
        self._write("mysite/urls.py", URLS_PY_I18N)
        self.run_command(mode="hybrid")

        urls_text = self._read("mysite/urls.py")
        self.assertIn('urlpatterns += i18n_patterns(\n    path("", include("cms.urls")),\n)', urls_text)
        # The CMS catch-all stays last, after the project's existing i18n block.
        self.assertLess(urls_text.index('include("accounts.urls")'), urls_text.index('include("cms.urls")'))
        # The headless API route is not language-prefixed: it joins the plain list.
        api_pos = urls_text.index('include("djangocms_rest.urls")')
        self.assertLess(api_pos, urls_text.index("i18n_patterns("))

    def test_cms_urls_join_plain_list_without_i18n_patterns(self):
        # Without i18n_patterns the catch-all simply joins the plain list and
        # no i18n_patterns block is introduced.
        self.run_command()

        urls_text = self._read("mysite/urls.py")
        self.assertIn('path("", include("cms.urls"))', urls_text)
        self.assertNotIn("i18n_patterns", urls_text)

    def test_i18n_urls_rerun_is_idempotent(self):
        self._write("mysite/urls.py", URLS_PY_I18N)
        self.run_command(mode="hybrid")
        urls_text = self._read("mysite/urls.py")

        self.run_command(mode="hybrid")
        self.assertEqual(self._read("mysite/urls.py"), urls_text)
        # The catch-all was added exactly once.
        self.assertEqual(urls_text.count('include("cms.urls")'), 1)

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

    def test_missing_settings_file_fails_cleanly(self):
        # manage.py still resolves to "mysite.settings", but the settings file
        # itself is gone: the command must fail with a clear message rather than
        # blowing up while reading a missing file.
        os.remove("mysite/settings.py")
        with self.assertRaises(CommandError) as raised:
            self.run_command()
        self.assertIn("Cannot locate the settings file", str(raised.exception))

    def test_missing_urls_file_degrades_gracefully(self):
        # ROOT_URLCONF points at "mysite.urls" but the file is gone. The settings
        # edits must still be applied and the install step still reached; the
        # missing urls only produces a warning, not a crash.
        os.remove("mysite/urls.py")
        command = self.run_command()
        self.assertIn('"cms",', self._read("mysite/settings.py"))
        self.assertIn("Could not locate the urls file", command.stderr.getvalue())
        command._finish_existing_project.assert_called_once()

    def test_computed_installed_apps_recovery(self):
        # INSTALLED_APPS is built from other lists (DJANGO_APPS + THIRD_PARTY_APPS),
        # so there is no literal list to splice into. The command must recover by
        # appending a reassignment rather than silently doing nothing.
        self._write("mysite/settings.py", COMPUTED_APPS_SETTINGS_PY)
        command = self.run_command()
        settings_text = self._read("mysite/settings.py")

        # The original computed assignment is preserved...
        self.assertIn("INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS", settings_text)
        # ...and the plain apps are added through an appended reassignment.
        self.assertIn("INSTALLED_APPS = INSTALLED_APPS + [", settings_text)
        self.assertIn('"cms",', settings_text)
        self.assertIn('"menus",', settings_text)

        # The admin style is anchored on django.contrib.admin, which lives in the
        # DJANGO_APPS literal, so it is still placed precisely (not in the wrap block).
        self.assertLess(
            settings_text.index("djangocms_simple_admin_style"),
            settings_text.index("django.contrib.admin"),
        )
        self.assertNotIn("djangocms_simple_admin_style", settings_text.split("INSTALLED_APPS = INSTALLED_APPS")[1])

        # The user is warned to review the appended block.
        self.assertIn("INSTALLED_APPS is a computed value", command.stderr.getvalue())

        # Packages are still derived from all matched apps.
        self.assertIn("cms", command._finish_existing_project.call_args.args[0])

    def test_computed_installed_apps_rerun_is_idempotent(self):
        self._write("mysite/settings.py", COMPUTED_APPS_SETTINGS_PY)
        self.run_command()
        settings_text = self._read("mysite/settings.py")

        self.run_command()
        self.assertEqual(self._read("mysite/settings.py"), settings_text)
        # The recovery reassignment was appended exactly once.
        self.assertEqual(settings_text.count("INSTALLED_APPS = INSTALLED_APPS + ["), 1)

    def test_dry_run_makes_no_changes_and_shows_diff(self):
        # --dry-run must leave every file untouched and report the planned edits
        # purely as unified diffs (no per-item summary).
        settings_before = self._read("mysite/settings.py")
        urls_before = self._read("mysite/urls.py")
        command = self.run_command(dry_run=True)

        self.assertEqual(self._read("mysite/settings.py"), settings_before)
        self.assertEqual(self._read("mysite/urls.py"), urls_before)
        self.assertFalse(os.path.isdir("templates"))

        out = command.stdout.getvalue()
        self.assertIn("Dry run", out)
        # The diff is the whole report -- the per-item summary is gone.
        self.assertNotIn("  + INSTALLED_APPS:", out)
        self.assertNotIn("Updated mysite/", out)
        # settings.py change shown as a diff
        self.assertIn("--- mysite/settings.py", out)
        self.assertIn('+    "cms",', out)
        # the base template that would be created shows as a new-file diff
        self.assertIn("+++ templates/cms-base.html", out)
        self.assertIn("/dev/null", out)
        # urls.py change shown as a diff
        self.assertIn("--- mysite/urls.py", out)
        self.assertIn('include("cms.urls")', out)

    def test_interactive_decline_makes_no_changes(self):
        # Declining the "Continue?" prompt must abort before anything is read or
        # written -- the rules are not even fetched and both files stay byte-identical.
        command = make_command()
        command.load_install_rules = mock.Mock(return_value=bundled_rules())
        command._finish_existing_project = mock.Mock()
        command.ask_bool = mock.Mock(return_value=False)
        command.add_to_existing_project({**DEFAULT_OPTIONS, "interactive": True})
        self.assertEqual(self._read("mysite/settings.py"), SETTINGS_PY)
        self.assertEqual(self._read("mysite/urls.py"), URLS_PY)
        self.assertIn("Aborted", command.stdout.getvalue())
        command.load_install_rules.assert_not_called()
        command._finish_existing_project.assert_not_called()


class HandleValidationTests(SimpleTestCase):
    def test_moderation_requires_versioning(self):
        command = make_command()
        command.load_install_rules = mock.Mock(return_value=bundled_rules())
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

    def test_dry_run_rejected_for_new_project(self):
        command = make_command()
        command.load_install_rules = mock.Mock(return_value=bundled_rules())
        options = {
            "name": "mysite",
            "directory": None,
            "interactive": False,
            "prompt": False,
            "template": None,
            "mode": "traditional",
            "versioning": True,
            "moderation": False,
            "alias": True,
            "stories": False,
            "dry_run": True,
        }
        with self.assertRaises(CommandError) as raised:
            command.handle(**options)
        self.assertIn("--dry-run is only supported", str(raised.exception))

    def test_missing_name_with_noinput(self):
        command = make_command()
        command.load_install_rules = mock.Mock(return_value=bundled_rules())
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

    def test_missing_name_without_input_fails_cleanly(self):
        command = make_command()
        command.load_install_rules = mock.Mock(return_value=bundled_rules())
        options = {
            "name": None,
            "directory": None,
            "interactive": True,
            "prompt": False,
            "template": None,
            "mode": None,
            "versioning": None,
            "moderation": None,
            "alias": None,
            "stories": None,
            "history": None,
        }
        with mock.patch("builtins.input", side_effect=EOFError), self.assertRaises(CommandError) as raised:
            command.handle(**options)
        self.assertIn("Input is not available", str(raised.exception))
