import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import TestCase


class NativeBackendPackagingTests(TestCase):
    def test_invalid_backend_reports_check_error_without_importing_treebeard(self):
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
urls = types.ModuleType("invalid_backend_test_urls")
urls.urlpatterns = []
sys.modules[urls.__name__] = urls

from django.conf import settings
settings.configure(
    SECRET_KEY="invalid-backend-test",
    ROOT_URLCONF=urls.__name__,
    CMS_TREE_BACKEND="typo",
    SITE_ID=1,
    CMS_TEMPLATES=[("base.html", "Base")],
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.sites",
        "cms",
        "menus",
        "sekizai",
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
                    "django.template.context_processors.request",
                ],
            },
        }
    ],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)

import django
django.setup()

from django.core.management import call_command
from django.core.management.base import SystemCheckError

try:
    call_command("check", verbosity=0)
except SystemCheckError as error:
    assert "cms.E002" in str(error), error
else:
    raise AssertionError("invalid backend passed system checks")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

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

    def test_project_install_rules_keep_native_backend_opt_in(self):
        rules_path = (
            Path(__file__).parents[1]
            / "management"
            / "commands"
            / "djangocms_install_rules.json"
        )
        rules = json.loads(rules_path.read_text())
        treebeard_rule = next(
            rule
            for rule in rules["installed_apps"]
            if "treebeard" in rule["items"]
        )
        backend_rule = next(
            rule
            for rule in rules["settings"]
            if rule["name"] == "CMS_TREE_BACKEND"
        )

        self.assertFalse(rules["options"]["native_tree"]["default"])
        self.assertEqual(treebeard_rule["when"], {"not_flag": "native_tree"})
        self.assertEqual(
            backend_rule["snippet"],
            'CMS_TREE_BACKEND = "mptree"',
        )
        self.assertEqual(backend_rule["when"], {"flag": "native_tree"})

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
call_command(
    "migrate",
    "cms",
    "0001_initial_squashed_0022_auto_20180620_1551",
    verbosity=0,
    interactive=False,
)
call_command("migrate", verbosity=0, interactive=False)

from django.contrib.sites.models import Site
from cms.models import Page

site = Site.objects.get_current()
root = Page.add_root(instance=Page(site=site))
first = root.add_child(site=site)
second = root.add_child(site=site)
second.move(first, "left")
Page.fix_tree()
assert Page.validate_tree() == []
first.delete()
root.refresh_from_db()
assert root.numchild == 1
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
