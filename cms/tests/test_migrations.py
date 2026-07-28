import importlib
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase, override_settings

from cms.api import create_page, create_page_content
from cms.models import PageContent
from cms.test_utils.testcases import CMSTestCase


class MigrationTestCase(TestCase):

    @override_settings(MIGRATION_MODULES={})
    def test_for_missing_migrations(self):
        output = StringIO()
        options = {
            'interactive': False,
            'dry_run': True,
            'stdout': output,
            'check_changes': True,
        }

        try:
            call_command('makemigrations', 'cms', **options)
        except SystemExit as e:
            status_code = str(e)
        else:
            # the "no changes" exit code is 0
            status_code = '0'

        if status_code == '1':
            self.fail(f'There are missing migrations:\n {output.getvalue()}')  # TODO: reactivate this line


class CopyUrlsToContentMigrationTestCase(CMSTestCase):
    """Exercises the data migration of 0044 against the current model state.

    The forward function only touches fields that exist unchanged in the
    current schema, so it can run against the live app registry.
    """

    def _run_migration(self):
        migration = importlib.import_module("cms.migrations.0044_pagecontent_slug_overwrite_url")
        migration._copy_urls_to_content(apps, None)

    def test_copies_urls_onto_contents(self):
        managed = create_page("Managed", "nav_playground.html", "en", slug="managed")
        overwritten = create_page("Overwritten", "nav_playground.html", "en", slug="overwritten")
        overwritten.urls.filter(language="en").update(managed=False, path="custom/path")
        orphan = create_page("Orphan", "nav_playground.html", "en", slug="orphan")
        orphan.urls.all().delete()

        # Simulate the pre-migration state where the content rows do not yet
        # carry the authored URL values.
        PageContent.objects.update(slug="stale", overwrite_url="stale")

        self._run_migration()

        managed_content = PageContent.objects.get(page=managed, language="en")
        self.assertEqual(managed_content.slug, "managed")
        self.assertIsNone(managed_content.overwrite_url)

        overwritten_content = PageContent.objects.get(page=overwritten, language="en")
        self.assertEqual(overwritten_content.slug, "overwritten")
        self.assertEqual(overwritten_content.overwrite_url, "custom/path")

        # Contents without a matching PageUrl keep their values
        orphan_content = PageContent.objects.get(page=orphan, language="en")
        self.assertEqual(orphan_content.slug, "stale")
        self.assertEqual(orphan_content.overwrite_url, "stale")

    def test_copies_urls_per_language(self):
        page = create_page("English", "nav_playground.html", "en", slug="english")
        create_page_content("de", "Deutsch", page, slug="deutsch")

        PageContent.objects.update(slug="stale", overwrite_url="stale")

        self._run_migration()

        self.assertEqual(PageContent.objects.get(page=page, language="en").slug, "english")
        self.assertEqual(PageContent.objects.get(page=page, language="de").slug, "deutsch")
