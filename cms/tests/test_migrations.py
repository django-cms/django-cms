import importlib
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.db import IntegrityError, connection, migrations, models, transaction
from django.db.migrations.state import ProjectState
from django.test import TestCase, TransactionTestCase, override_settings

from cms.api import create_page, create_page_content
from cms.models import PageContent
from cms.test_utils.testcases import CMSTestCase

migration_0044 = importlib.import_module("cms.migrations.0044_pagecontent_slug_overwrite_url")


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
        migration_0044._copy_urls_to_content(apps, None)

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


class AddFieldKeepingDatabaseUniquenessTestCase(TransactionTestCase):
    """Regression tests for the ``AddField`` guard of 0044 (#8776).

    A versioning package may drop ``PageContent``'s ``("language", "page")``
    unique constraint from the database without being able to remove it from
    the migration state. SQLite rebuilds a table from that state whenever a
    non-null column is added, so a plain ``AddField`` recreates the constraint
    and then trips over the rows the versioning package stores per version.

    The operation is exercised against a throwaway model of the same shape so
    that the test does not depend on migrations being enabled.
    """

    app_label = "cms"
    model_name = "AddFieldGuardModel"

    def create_table(self):
        operation = migrations.CreateModel(
            name=self.model_name,
            fields=[
                ("id", models.AutoField(primary_key=True)),
                ("language", models.CharField(max_length=15)),
                ("page", models.IntegerField()),
            ],
            options={"unique_together": {("language", "page")}},
        )
        before, after = ProjectState(), ProjectState()
        operation.state_forwards(self.app_label, after)
        with connection.schema_editor() as schema_editor:
            operation.database_forwards(self.app_label, schema_editor, before, after)
        self.addCleanup(self.drop_table, after)
        return after

    def drop_table(self, state):
        operation = migrations.DeleteModel(self.model_name)
        after = state.clone()
        operation.state_forwards(self.app_label, after)
        with connection.schema_editor() as schema_editor:
            operation.database_forwards(self.app_label, schema_editor, state, after)

    def add_slug(self, before):
        """Add a non-null column, the case that makes SQLite rebuild the table."""
        operation = migration_0044.AddFieldKeepingDatabaseUniqueness(
            model_name=self.model_name,
            name="slug",
            field=models.SlugField(default="", max_length=255),
            preserve_default=False,
        )
        after = before.clone()
        operation.state_forwards(self.app_label, after)
        with connection.schema_editor() as schema_editor:
            operation.database_forwards(self.app_label, schema_editor, before, after)
        return after.apps.get_model(self.app_label, self.model_name)

    def drop_unique_constraint(self, state):
        """Do what djangocms-versioning's 0009 does: drop it in the database only."""
        model = state.apps.get_model(self.app_label, self.model_name)
        with connection.schema_editor() as schema_editor:
            schema_editor.alter_unique_together(model, {("language", "page")}, set())
        return model

    def has_unique_constraint(self, model):
        with connection.schema_editor() as schema_editor:
            return migration_0044._has_unique_constraint(schema_editor, model, ("language", "page"))

    def test_does_not_restore_a_constraint_the_database_dropped(self):
        state = self.create_table()
        model = self.drop_unique_constraint(state)
        model.objects.create(language="en", page=1)
        model.objects.create(language="en", page=1)

        new_model = self.add_slug(state)

        self.assertFalse(self.has_unique_constraint(new_model))
        self.assertEqual(new_model.objects.count(), 2)
        # Existing rows receive the default of the new column
        self.assertEqual(list(new_model.objects.values_list("slug", flat=True)), ["", ""])

    def test_keeps_a_constraint_the_database_still_has(self):
        state = self.create_table()
        model = state.apps.get_model(self.app_label, self.model_name)
        model.objects.create(language="en", page=1)

        new_model = self.add_slug(state)

        self.assertTrue(self.has_unique_constraint(new_model))
        with self.assertRaises(IntegrityError), transaction.atomic():
            new_model.objects.create(language="en", page=1, slug="duplicate")
