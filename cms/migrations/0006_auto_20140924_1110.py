from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0005_auto_20140924_1039'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={'ordering': ('path',), 'verbose_name': 'page', 'verbose_name_plural': 'pages', 'permissions': (('view_page', 'Can view page'), ('publish_page', 'Can publish page'), ('edit_static_placeholder', 'Can edit static placeholders'))},
        ),
        migrations.RemoveField(
            model_name='cmsplugin',
            name='level',
        ),
        migrations.RemoveField(
            model_name='cmsplugin',
            name='lft',
        ),
        migrations.RemoveField(
            model_name='cmsplugin',
            name='rght',
        ),
        migrations.RemoveField(
            model_name='cmsplugin',
            name='tree_id',
        ),
        migrations.RemoveField(
            model_name='page',
            name='level',
        ),
        migrations.RemoveField(
            model_name='page',
            name='lft',
        ),
        migrations.RemoveField(
            model_name='page',
            name='rght',
        ),
        migrations.RemoveField(
            model_name='page',
            name='tree_id',
        ),
        migrations.AlterField(
            model_name='cmsplugin',
            name='depth',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='cmsplugin',
            name='numchild',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='cmsplugin',
            name='path',
            field=models.CharField(unique=True, max_length=255, editable=False),
        ),
    ]
