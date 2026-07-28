from django.db import migrations, models
from django.db.models import Case, Exists, F, OuterRef, Subquery, Value, When


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
        migrations.AddField(
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
        migrations.AddField(
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
