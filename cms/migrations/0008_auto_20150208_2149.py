from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0007_auto_20141028_1559'),
    ]

    operations = [
        migrations.AlterField(
            model_name='title',
            name='redirect',
            field=models.CharField(max_length=2048, null=True, verbose_name='redirect', blank=True),
            preserve_default=True,
        ),
    ]
