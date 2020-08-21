from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0020_old_tree_cleanup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='title',
            name='meta_description',
            field=models.TextField(blank=True, help_text='The text displayed in search engines.', null=True, verbose_name='description'),
        ),
    ]
