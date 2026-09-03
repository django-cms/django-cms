from django.db import migrations, models
from django.db.models import Case, Exists, F, OuterRef, Subquery, Value, When


def _has_unique_constraint(schema_editor, model, field_names):
    """Return whether the database really enforces uniqueness over ``field_names``."""
    columns = {model._meta.get_field(name).column for name in field_names}
    with schema_editor.connection.cursor() as cursor:
        constraints = schema_editor.connection.introspection.get_constraints(cursor, model._meta.db_table)
    return any(
        constraint["unique"] and not constraint.get("primary_key") and set(constraint["columns"]) == columns
        for constraint in constraints.values()
    )


class AddFieldKeepingDatabaseUniqueness(migrations.AddField):
    """``AddField`` that never resurrects a unique constraint the database dropped.

    ``PageContent`` carries ``unique_together = (("language", "page"),)`` in the
    migration state, but djangocms-versioning removes that constraint from the
    database only (its ``0009_cms_pagecontent_remove_unique_constraint`` does the
    work in a ``RunPython``, which cannot alter another app's state). Versioning
    then stores one row per version, so several rows share a page and language.

    SQLite cannot ``ALTER TABLE ADD COLUMN`` a non-null column and rebuilds the
    whole table from the state model instead. That rebuild would recreate the
    stale constraint and fail while copying the versioned rows over. So drop
    ``unique_together`` for the duration of the rebuild whenever the database
    turns out not to have the constraint anyway. Installations without a
    versioning package still have it and keep it.

    See django-cms#8776; djangocms-versioning#599 tracks reconciling state and
    database for good.
    """

    unique_together = (("language", "page"),)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        from_model = from_state.apps.get_model(app_label, self.model_name)
        to_model = to_state.apps.get_model(app_label, self.model_name)

        if not self.allow_migrate_model(schema_editor.connection.alias, to_model) or _has_unique_constraint(
            schema_editor, from_model, self.unique_together[0]
        ):
            super().database_forwards(app_label, schema_editor, from_state, to_state)
            return

        originals = [(model, model._meta.unique_together) for model in (from_model, to_model)]
        for model, original in originals:
            model._meta.unique_together = tuple(
                fields for fields in original if tuple(fields) not in self.unique_together
            )
        try:
            super().database_forwards(app_label, schema_editor, from_state, to_state)
        finally:
            for model, original in originals:
                model._meta.unique_together = original


def _copy_urls_to_content(apps, schema_editor):
    """Copy the authored URL values from the (unversioned) PageUrl objects onto
    every PageContent object of the same page and language.

    All versions of a page content implicitly shared one URL before this
    migration, so every version receives the currently effective slug and
    overwrite URL.
    """
    PageContent = apps.get_model("cms", "PageContent")
    PageUrl = apps.get_model("cms", "PageUrl")

    url_qs = PageUrl.objects.filter(page_id=OuterRef("page_id"), language=OuterRef("language"))
    PageContent.objects.filter(Exists(url_qs)).update(
        slug=Subquery(url_qs.values("slug")[:1]),
        overwrite_url=Subquery(
            url_qs.annotate(
                overwrite=Case(
                    When(managed=True, then=Value(None)),
                    default=F("path"),
                    output_field=models.CharField(),
                )
            ).values("overwrite")[:1]
        ),
    )


def _noop(apps, schema_editor):
    # The PageUrl objects still hold the published values; removing the fields
    # loses only draft-specific edits made after migrating forward.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0043_alter_globalpagepermission_can_view_and_more"),
    ]

    operations = [
        AddFieldKeepingDatabaseUniqueness(
            model_name="pagecontent",
            name="slug",
            field=models.SlugField(
                default="",
                help_text="The part of the title that is used in the URL",
                max_length=255,
                verbose_name="slug",
            ),
            preserve_default=False,
        ),
        AddFieldKeepingDatabaseUniqueness(
            model_name="pagecontent",
            name="overwrite_url",
            field=models.CharField(
                blank=True,
                help_text="Keep this field empty if standard path should be used.",
                max_length=255,
                null=True,
                verbose_name="overwrite URL",
            ),
        ),
        migrations.RunPython(_copy_urls_to_content, _noop, elidable=False),
    ]
