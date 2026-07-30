import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import TestCase


class NativeBackendPackagingTests(TestCase):
    def test_historical_migration_imports_without_treebeard(self):
        script = """
import builtins
import importlib

real_import = builtins.__import__

def import_without_treebeard(name, *args, **kwargs):
    if name == "treebeard" or name.startswith("treebeard."):
        raise AssertionError(f"unexpected treebeard import: {name}")
    return real_import(name, *args, **kwargs)

builtins.__import__ = import_without_treebeard
importlib.import_module("cms.migrations.0005_auto_20140924_1039")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_project_install_rules_select_native_backend_without_treebeard_app(self):
        rules_path = (
            Path(__file__).parents[1]
            / "management"
            / "commands"
            / "djangocms_install_rules.json"
        )
        rules = json.loads(rules_path.read_text())
        installed_apps = {
            app
            for rule in rules["installed_apps"]
            for app in rule["items"]
        }
        settings_by_name = {
            rule["name"]: rule["snippet"]
            for rule in rules["settings"]
        }

        self.assertNotIn("treebeard", installed_apps)
        self.assertEqual(
            settings_by_name["CMS_TREE_BACKEND"],
            'CMS_TREE_BACKEND = "mptree"',
        )

    def test_treebeard_is_a_compatibility_extra_not_a_core_dependency(self):
        pyproject = (Path(__file__).parents[2] / "pyproject.toml").read_text()
        core_dependencies = pyproject.split("dependencies = [", 1)[1].split("]", 1)[0]
        optional_dependencies = pyproject.split("[project.optional-dependencies]", 1)[1]

        self.assertNotIn("django-treebeard", core_dependencies)
        self.assertIn(
            'treebeard = ["django-treebeard >=4.3"]',
            optional_dependencies,
        )

    def test_native_backend_checks_and_migrates_without_treebeard(self):
        script = """
import builtins
import sys
import types

real_import = builtins.__import__

def import_without_treebeard(name, *args, **kwargs):
    if name == "treebeard" or name.startswith("treebeard."):
        raise AssertionError(f"unexpected treebeard import: {name}")
    return real_import(name, *args, **kwargs)

builtins.__import__ = import_without_treebeard

urls = types.ModuleType("native_backend_test_urls")
urls.urlpatterns = []
sys.modules[urls.__name__] = urls

from django.conf import settings
settings.configure(
    SECRET_KEY="native-backend-test",
    ROOT_URLCONF=urls.__name__,
    CMS_TREE_BACKEND="mptree",
    SITE_ID=1,
    CMS_TEMPLATES=[("base.html", "Base")],
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.admin",
        "django.contrib.sites",
        "django.contrib.staticfiles",
        "django.contrib.messages",
        "cms",
        "menus",
        "sekizai",
    ],
    MIDDLEWARE=[
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                    "django.template.context_processors.request",
                ],
            },
        }
    ],
    STATIC_URL="/static/",
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)

import django
django.setup()

from django.core.management import call_command
call_command("check", verbosity=0)
call_command("migrate", verbosity=0, interactive=False)
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
