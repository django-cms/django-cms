import copy
import json
import os
import re
import shutil
import tempfile
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.template import Context, Template
from django.test import SimpleTestCase, override_settings

import cms

MANIFEST_BACKEND = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

CMS_TEMPLATE_DIR = os.path.join(os.path.dirname(cms.__file__), "templates")

# {% static "path/to/file.ext" %} / {% static_with_version "path/to/file.ext" %}
STATIC_TAG_RE = re.compile(
    r"{%\s*(?P<tag>static|static_with_version)\s+"
    r"(?P<quote>[\"'])(?P<path>[^\"']+)(?P=quote)\s*%}"
)


def iter_template_static_tags():
    """
    Yield ``(template, tag)`` tuples for every static file reference with a
    literal path found in the templates shipped with django CMS. Paths built
    from template variables or filters are skipped, they cannot be resolved
    without a rendering context.
    """
    for dirpath, _, filenames in os.walk(CMS_TEMPLATE_DIR):
        for filename in sorted(filenames):
            if not filename.endswith(".html"):
                continue
            template = os.path.join(dirpath, filename)
            with open(template, encoding="utf-8") as fobj:
                contents = fobj.read()
            for match in STATIC_TAG_RE.finditer(contents):
                yield os.path.relpath(template, CMS_TEMPLATE_DIR), match.group(0)


class ManifestStaticFilesTestCase(SimpleTestCase):
    """
    Projects commonly run ``collectstatic`` with Django's
    ``ManifestStaticFilesStorage``. Contrary to the plain storage backend it
    hashes every collected file and looks up references in a manifest, which
    turns a dangling reference into a hard error instead of a 404.

    ``DEBUG`` is turned off for these tests, as the manifest storage bypasses
    the manifest lookup entirely while ``DEBUG`` is on.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.static_root = tempfile.mkdtemp(prefix="cms-manifest-static-")
        cls.addClassCleanup(shutil.rmtree, cls.static_root, ignore_errors=True)

        storages = copy.deepcopy(settings.STORAGES)
        storages["staticfiles"]["BACKEND"] = MANIFEST_BACKEND
        overridden_settings = override_settings(
            DEBUG=False,
            STATIC_ROOT=cls.static_root,
            STORAGES=storages,
        )
        overridden_settings.enable()
        cls.addClassCleanup(overridden_settings.disable)

        # A dangling reference inside a collected css/js file makes
        # post-processing - and with it the management command - fail.
        out = StringIO()
        call_command(
            "collectstatic",
            interactive=False,
            clear=True,
            verbosity=0,
            stdout=out,
            stderr=out,
        )
        cls.collectstatic_output = out.getvalue()

    def test_collectstatic_writes_manifest(self):
        """``collectstatic`` post-processes the static files shipped by the CMS."""
        manifest_path = os.path.join(self.static_root, "staticfiles.json")

        self.assertTrue(
            os.path.exists(manifest_path),
            f"No staticfiles manifest was written: {self.collectstatic_output}",
        )
        with open(manifest_path, encoding="utf-8") as fobj:
            manifest = json.load(fobj)["paths"]

        cms_files = {path: name for path, name in manifest.items() if path.startswith("cms/")}
        self.assertTrue(cms_files, "No django CMS static files were collected")
        for path, hashed_name in cms_files.items():
            with self.subTest(path=path):
                self.assertTrue(
                    os.path.exists(os.path.join(self.static_root, hashed_name)),
                    f"{path} is in the manifest, but {hashed_name} was not collected",
                )

    def test_template_static_references_resolve(self):
        """
        Every static file referenced by a django CMS template can be resolved
        against the manifest. A missing entry raises a ``ValueError`` and makes
        the whole template fail to render.
        """
        tags = list(iter_template_static_tags())

        self.assertTrue(tags, "No static file references found in the CMS templates")
        for template, tag in tags:
            with self.subTest(template=template, tag=tag):
                source = "{% load static cms_static %}" + tag
                # Raises ValueError for files missing from the manifest
                Template(source).render(Context({}))
