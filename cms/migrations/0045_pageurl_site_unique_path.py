import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Count, Min, OuterRef, Subquery


def _fill_site(apps, schema_editor):
    """Denormalize the page's site onto every PageUrl row."""
    Page = apps.get_model("cms", "Page")
    PageUrl = apps.get_model("cms", "PageUrl")

    PageUrl.objects.update(
        site=Subquery(Page.objects.filter(pk=OuterRef("page_id")).values("site")[:1])
    )


def _resolve_duplicate_paths(apps, schema_editor):
    """Resolve pre-existing duplicate paths so the unique constraint can be
    added.

    Duplicates could only be created by race conditions the constraint now
    prevents; of each set only one page (arbitrarily, the first) was actually
    served. That row keeps the path, the others are set to ``path=None``
    (unreachable) and regain a path when they are saved or published next.
    """
    PageUrl = apps.get_model("cms", "PageUrl")

    duplicates = (
        PageUrl.objects.filter(path__isnull=False)
        .values("site_id", "language", "path")
        .annotate(count=Count("pk"), first_pk=Min("pk"))
        .filter(count__gt=1)
    )
    for duplicate in duplicates.iterator():
        PageUrl.objects.filter(
            site_id=duplicate["site_id"],
            language=duplicate["language"],
            path=duplicate["path"],
        ).exclude(pk=duplicate["first_pk"]).update(path=None)


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0044_pagecontent_slug_overwrite_url"),
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="pageurl",
            name="site",
            field=models.ForeignKey(
                null=True,
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="djangocms_urls",
                to="sites.site",
                verbose_name="site",
            ),
        ),
        migrations.RunPython(_fill_site, migrations.RunPython.noop, elidable=False),
        migrations.AlterField(
            model_name="pageurl",
            name="site",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="djangocms_urls",
                to="sites.site",
                verbose_name="site",
            ),
        ),
        migrations.RunPython(_resolve_duplicate_paths, migrations.RunPython.noop, elidable=False),
        migrations.AddConstraint(
            model_name="pageurl",
            constraint=models.UniqueConstraint(
                fields=("site", "language", "path"), name="unique_site_language_path"
            ),
        ),
    ]
