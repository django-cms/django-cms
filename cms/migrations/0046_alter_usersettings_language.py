from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0045_pageurl_site_unique_path"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usersettings",
            name="language",
            field=models.CharField(
                choices=settings.LANGUAGES,
                help_text="The language for the admin interface and toolbar",
                max_length=15,
                verbose_name="Language",
            ),
        ),
    ]
